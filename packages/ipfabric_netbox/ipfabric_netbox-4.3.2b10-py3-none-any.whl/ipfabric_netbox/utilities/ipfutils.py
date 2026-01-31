import json
import logging
from collections import Counter
from copy import deepcopy
from functools import cache
from importlib import metadata
from typing import Callable
from typing import TYPE_CHECKING
from typing import TypeVar

from core.exceptions import SyncError
from core.signals import clear_events
from dcim.models import Device
from dcim.models import Site
from dcim.models import VirtualChassis
from dcim.signals import assign_virtualchassis_master
from dcim.signals import sync_cached_scope_fields
from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.db.models import signals
from django.utils.text import slugify
from django_tables2 import Column
from extras.events import flush_events
from ipfabric import IPFClient
from jinja2.sandbox import SandboxedEnvironment
from netbox.config import get_config
from netbox.context import events_queue
from netutils.utils import jinja2_convenience_function

from ..choices import IPFabricSourceTypeChoices
from ..choices import IPFabricSyncStatusChoices
from ..exceptions import IPAddressDuplicateError
from ..exceptions import IPAddressPrimaryAssignmentError
from ..exceptions import IPAddressPrimaryRemovalError
from ..exceptions import RequiredDependencyFailedSkip
from ..exceptions import SearchError
from ..exceptions import SyncDataError


if TYPE_CHECKING:
    from ..models import IPFabricIngestion
    from ..models import IPFabricIngestionIssue
    from ipam.models import IPAddress
    from ..models import IPFabricTransformMap
    from ..models import IPFabricSync

logger = logging.getLogger("ipfabric_netbox.utilities.ipf_utils")

ModelTypeVar = TypeVar("ModelTypeVar", bound=Model)


def slugify_text(value):
    return slugify(value)


device_serial_max_length = Device._meta.get_field("serial").max_length


def serial(data: dict) -> str:
    sn_length = len(data.get("sn"))
    serial_number = data.get("sn") if sn_length < device_serial_max_length else ""
    if not serial_number:
        serial_number = data.get("id")
    return serial_number


IPF_JINJA_FILTERS = {"slugify": slugify_text, "serial": serial}


def render_jinja2(template_code, context):
    """
    Render a Jinja2 template with the provided context. Return the rendered content.
    """
    environment = SandboxedEnvironment()
    environment.filters.update(get_config().JINJA2_FILTERS)
    environment.filters.update(IPF_JINJA_FILTERS)
    environment.filters.update(jinja2_convenience_function())
    return environment.from_string(source=template_code).render(**context)


class EventsClearer:
    """
    Handles clearing of events after defined number of objects are saved to reduce memory usage.
    ChangeLoggingMiddleware causes rest_framework Fields to be held in memory for the whole
    duration of current request. This causes high memory usage during sync jobs.

    The data is already written in DB due to branching ChangeDiff. So we can trigger
    the events clearing here to free up memory.

    For performance reasons we don't want to clear the event cache after every object is saved,
    but we also don't want to wait until the end of the sync when syncing large number of objects.
    This class helps to clear events after a defined threshold is reached.

    Without it, the memory requirements are roughly 1,5GB per 10k changes.
    """

    def __init__(self, sender: object, threshold: int = 100) -> None:
        self.sender = sender
        self.threshold = threshold
        self.counter = 0

    def increment(self) -> None:
        """
        Increment the counter and clear events if threshold is reached.

        This should not be called after every instance.snapshot() but instead
        when the instance is processed. This makes sure it's changes are synced
        as a whole. Calling it after every single snapshot() causes issues.
        """
        self.counter += 1
        if self.counter >= self.threshold:
            self.clear()

    def clear(self) -> None:
        logger.debug("Clearing events to reduce memory usage.")
        # This makes sure webhooks are sent properly
        if events := list(events_queue.get().values()):
            flush_events(events)
        # And now the queue can be cleared
        clear_events.send(sender=None)
        self.counter = 0


class IPFabric(object):
    def __init__(self, parameters=None) -> None:
        if parameters:
            self.ipf = IPFClient(**parameters, unloaded=True)
        else:
            self.ipf = IPFClient(
                **settings.PLUGINS_CONFIG["ipfabric_netbox"], unloaded=True
            )
        self.ipf._client.headers[
            "user-agent"
        ] += f'; ipfabric-netbox/{metadata.version("ipfabric-netbox")}'  # noqa: E702

    def get_table_data(self, table, device):
        filter = {"sn": ["eq", device.serial]}
        split = table.split(".")

        if len(split) == 2:
            if split[1] == "serial_ports":
                table = getattr(self.ipf.technology, split[1])
            else:
                tech = getattr(self.ipf.technology, split[0])
                table = getattr(tech, split[1])
        else:
            table = getattr(self.ipf.inventory, split[0])

        columns = self.ipf.get_columns(table.endpoint)

        columns.pop(0)

        columns = [(k, Column()) for k in columns]
        data = table.all(
            filters=filter,
        )
        return data, columns


def make_hashable(obj):
    if isinstance(obj, dict):
        return tuple((k, make_hashable(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        return tuple(make_hashable(x) for x in obj)
    else:
        return obj


class DataRecord:
    """Contains all data required to sync single object to NetBox."""

    def __init__(
        self,
        model_string: str,
        data: dict,
        # These values are filled later as the record is passed down the pipeline
        context: dict | None = None,
        transform_map: "IPFabricTransformMap | None" = None,
    ):
        self.model_string = model_string
        self.data = data
        self.context = context or dict()
        self.transform_map = transform_map

    def __hash__(self):
        if self._hash is None:
            try:
                self._hash = hash(
                    (
                        self.model_string,
                        # Since the dicts are already ordered, it is safe to hash them
                        # .values() are mutable, this is fixed by tuple() to get same hash every time
                        make_hashable(self.data),
                        make_hashable(self.context),
                    )
                )
            except Exception as err:
                raise Exception(f"DATA: {self.data}") from err
        return self._hash

    def __eq__(self, other):
        return isinstance(other, DataRecord) and hash(self) == hash(other)

    # Make sure data and context are sorted by keys when stored to speed up hash calculation
    # This should be safe since they do not contain nested dicts
    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = {k: v for k, v in sorted(value.items())}
        self._hash = None  # Invalidate cached hash

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, value):
        self._context = {k: v for k, v in sorted(value.items())}
        self._hash = None  # Invalidate cached hash


def order_members(members: list[dict]) -> dict[str, list[dict]]:
    """Order VC members to dict, where key is master serial number and values are all members."""
    devices = {}

    for member in members:
        # Caution: If the snapshot is created in development mode, the `sn` field is calculated from loopback IP
        # This can be spotted by checking if `sn` is different from `memberSn` for the master device
        # Plus `sn` will be IP of loopback in hex...
        master_serial = member.get("sn")
        if master_serial and member.get("memberSn"):
            if master_serial in devices:
                devices[master_serial].append(member)
            else:
                devices[master_serial] = [member]

    return devices


def prepare_devices(
    devices: list[dict], members: dict[str, list[dict]]
) -> tuple[list[dict], list[dict]]:
    """
    Prepare devices list for syncing:
     - incorporating virtual chassis members
     - handle duplicate hostnames
    """

    hostnames = [d["hostname"] for d in devices]
    counter = Counter(hostnames)

    # All devices to be synced
    all_devices = []
    # All virtual chassis to be synced
    virtualchassis = []

    for device in devices[:]:
        if counter[device["hostname"]] > 1:
            device["hostname"] = f"{device['hostname']} - ({device['sn']})"
        if child_members := members.get(device.get("sn")):
            # This device is the VC master, and we're iterating over all it's members
            for child_member in child_members:
                # There is physically no device with hostname matching the virtual chassis
                # There are only members, so "hostname/1", "hostname/2", etc.
                new_device = deepcopy(device)
                new_device[
                    "hostname"
                ] = f"{device['hostname']}/{child_member.get('member')}"
                new_device["virtual_chassis"] = child_member
                if device.get("sn") != child_member.get("memberSn"):
                    # VC members (non-master) are not in Device table, need to add them as new Device
                    new_device["model"] = child_member.get("pn")
                    new_device["sn"] = child_member.get("memberSn")
                    all_devices.append(new_device)
                else:
                    # Master device, create the virtual chassis based on it
                    virtualchassis.append(child_member)
                    all_devices.append(new_device)
            hostnames = [d["hostname"] for d in devices]
            counter = Counter(hostnames)
        else:
            all_devices.append(device)
    return all_devices, virtualchassis


class IPFabricSyncRunner(object):
    def __init__(
        self,
        sync: "IPFabricSync",
        client: IPFClient = None,
        ingestion=None,
        settings: dict = None,
    ) -> None:
        self.client = client
        self.settings = settings
        self.ingestion = ingestion
        self.sync = sync
        self.transform_maps = sync.get_transform_maps(sync.parameters.get("groups"))
        if hasattr(self.sync, "logger"):
            self.logger = self.sync.logger

        if self.sync.snapshot_data.status != "loaded":
            raise SyncError("Snapshot not loaded in IP Fabric.")

        # Some objects depend on others being synced first, store errors to avoid duplicates
        # We should store all dependant objects, but it's very hard to do
        # For now store only serial numbers since that is the largest dependency chain
        self.error_serials = set()

        self.events_clearer = EventsClearer(sender=self.__class__, threshold=100)

    @staticmethod
    def get_error_serial(context: dict | None, data: dict | None) -> str | None:
        """Get error serial from context or raw data for skipping purposes."""
        context = context or {}
        data = data or {}
        return (
            context.get("sn") or context.get("serial") or serial(data)
            if "sn" in data
            else None
        )

    def create_or_get_sync_issue(
        self,
        exception: Exception,
        ingestion: "IPFabricIngestion",
        message: str = None,
        model_string: str = None,
        context: dict = None,
        data: dict = None,
    ) -> "tuple[bool, IPFabricIngestionIssue]":
        """
        Helper function to handle sync errors and create IPFabricIngestionIssue if needed.
        """
        context = context or {}

        error_serial = self.get_error_serial(context, data)
        # Ignore models that do not have any dependencies by serial number
        if error_serial and model_string not in ["ipam.ipaddress", "dcim.macaddress"]:
            self.error_serials.add(error_serial)

        # TODO: This is to prevent circular import issues, clean it up later.
        from ..models import IPFabricIngestionIssue

        if not hasattr(exception, "issue_id") or not exception.issue_id:
            issue = IPFabricIngestionIssue.objects.create(
                ingestion=ingestion,
                exception=exception.__class__.__name__,
                message=message or getattr(exception, "message", str(exception)),
                model=model_string,
                coalesce_fields={
                    k: v for k, v in context.items() if k not in ["defaults"]
                },
                defaults=context.get("defaults", dict()),
                raw_data=data or dict(),
            )
            if hasattr(exception, "issue_id"):
                exception.issue_id = issue.id
            return True, issue
        else:
            issue = IPFabricIngestionIssue.objects.get(id=exception.issue_id)
            return False, issue

    @staticmethod
    def handle_errors(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as err:
                # Log the error to logger outside of job - console/file
                logger.error(err, exc_info=True)
                if hasattr(err, "issue_id") and err.issue_id:
                    # The error is already logged to user, no need to log it again
                    return None
                # Logging section for logs inside job - facing user
                self = args[0]
                if isinstance(err, SearchError):
                    if self.settings.get(err.model_string):
                        self.logger.log_failure(
                            f"Aborting syncing `{err.model_string}` instance due to above error, please check your transform maps and/or existing data.",
                            obj=self.sync,
                        )
                    else:
                        self.logger.log_failure(
                            f"Syncing `{err.model_string}` is disabled in settings, but hit above error trying to find the correct item. Please check your transform maps and/or existing data.",
                            obj=self.sync,
                        )
                if isinstance(err, IPAddressDuplicateError):
                    self.logger.log_warning(
                        f"IP Address `{err.data.get('address')}` already exists in `{err.model_string}` with coalesce fields: `{err.coalesce_fields}`. Please check your transform maps and/or existing data.",
                        obj=self.sync,
                    )
                else:
                    self.logger.log_failure(
                        f"Syncing failed with: `{err}`. See above error for more details.",
                        obj=self.sync,
                    )
                # Make sure the whole sync is failed when we encounter error
                self.sync.status = IPFabricSyncStatusChoices.FAILED
                return None

        return wrapper

    def get_db_connection_name(self) -> str:
        connection_name = None
        if self.ingestion:
            connection_name = self.ingestion.branch.connection_name
        return connection_name

    def get_transform_context(self, record: DataRecord) -> DataRecord:
        if not record.transform_map:
            raise SystemError(f"No transform map available for {record.model_string}")
        try:
            record.context = record.transform_map.get_context(record.data)
        except Exception as err:
            message = f"Error getting context for `{record.model_string}`."
            if isinstance(err, ObjectDoesNotExist):
                message += (
                    " Could not find related object using template in transform maps."
                )
            elif isinstance(err, MultipleObjectsReturned):
                message += " Multiple objects returned using on template in transform maps, the template is not strict enough."
            _, issue = self.create_or_get_sync_issue(
                exception=err,
                ingestion=self.ingestion,
                message=message,
                model_string=record.model_string,
                data=record.data,
            )
            raise SearchError(
                message=message,
                data=record.data,
                model_string=record.model_string,
                issue_id=issue.pk,
            ) from err

        return record

    def get_model_or_update(self, record: DataRecord) -> ModelTypeVar | None:
        # First check if there are any previous errors linked to this object
        error_serial = self.get_error_serial(record.context, record.data)
        if error_serial and error_serial in self.error_serials:
            # We want to raise it as exception so it's shown in ingestion issues but can be filtered out.
            exception = RequiredDependencyFailedSkip(
                message=f"Skipping syncing of `{record.model_string}` with serial `{error_serial}` due to previous errors.",
                model_string=record.model_string,
                context=record.context,
                data=record.data,
            )
            _, issue = self.create_or_get_sync_issue(
                exception=exception,
                ingestion=self.ingestion,
                model_string=record.model_string,
                context=record.context,
                data=record.data,
            )
            raise exception
        record = self.get_transform_context(record)
        queryset = record.transform_map.target_model.model_class().objects
        model_settings = self.settings.get(f"{record.model_string}", False)

        obj = None
        try:
            connection_name = self.get_db_connection_name()
            if model_settings:
                logger.info(f"Creating {record.model_string}")
                obj = record.transform_map.update_or_create_instance(
                    context=record.context,
                    tags=self.sync.tags.all(),
                    connection_name=connection_name,
                )
            else:
                logger.info(f"Getting {record.model_string}")
                record.context.pop("defaults", None)
                obj = queryset.using(connection_name).get(**record.context)
        except queryset.model.DoesNotExist as err:
            message = f"Instance of `{record.model_string}` not found."
            _, issue = self.create_or_get_sync_issue(
                exception=err,
                ingestion=self.ingestion,
                message=message,
                model_string=record.model_string,
                context=record.context,
                data=record.data,
            )
            raise SearchError(
                message=message,
                model_string=record.model_string,
                context=record.context,
                data=record.data,
                issue_id=issue.pk,
            ) from err
        except queryset.model.MultipleObjectsReturned as err:
            message = f"Multiple instances of `{record.model_string}` found."
            _, issue = self.create_or_get_sync_issue(
                exception=err,
                ingestion=self.ingestion,
                message=message,
                model_string=record.model_string,
                context=record.context,
                data=record.data,
            )
            raise SearchError(
                message=message,
                model_string=record.model_string,
                context=record.context,
                data=record.data,
                issue_id=issue.pk,
            ) from err
        except Exception as err:
            _, issue = self.create_or_get_sync_issue(
                exception=err,
                ingestion=self.ingestion,
                model_string=record.model_string,
                context=record.context,
                data=record.data,
            )
            raise SyncDataError(
                model_string=record.model_string,
                context=record.context,
                data=record.data,
                issue_id=issue.pk,
            ) from err

        return obj

    def collect_data(self):
        # Importing here to avoid circular import
        from ..models import IPFabricEndpoint

        try:
            self.logger.log_info(
                "Collecting information from IP Fabric",
                obj=self.sync.snapshot_data.source,
            )
            data = {}
            # TODO: Replace endpoint value in SnapshotData with Endpoint link
            if self.sync.snapshot_data.source.type == IPFabricSourceTypeChoices.REMOTE:
                # This requires data already pushed to NetBox by user, does not connect to IPF directly
                self.logger.log_info(
                    "Remote collector checking for snapshot data.", obj=self.sync
                )
                if not self.sync.snapshot_data.ipf_data.count() > 0:
                    raise SyncError(
                        "No snapshot data available. This is a remote sync. Push data to NetBox first."
                    )
                for endpoint in IPFabricEndpoint.objects.all():
                    data[endpoint.endpoint] = list(
                        self.sync.snapshot_data.ipf_data.filter(
                            type=endpoint.endpoint
                        ).values_list("data", flat=True)
                    )
            else:
                # This pulls data directly from IP Fabric instance
                # TODO: If certain columns are not enabled in IPF, sync will fail in odd ways
                #  For example missing `nameOriginal` on Interface makes it unable to sync IPs
                #  When pulling from endpoint, make sure to specify columns according to transform maps
                #  This can be pulled using logic in IPFabricTransformMap.strip_source_data()
                # TODO: Also cache it to improve performance, no need to regex every time!
                self.logger.log_info(
                    "Local collector being used for snapshot data.", obj=self.sync
                )
                enabled_models = [
                    param
                    for param in self.sync.parameters.keys()
                    if "." in param and self.sync.parameters.get(param) is True
                ]
                # Always pull devices for now since other models depend on them
                enabled_models.append("dcim.device")
                # Interfaces are required for IP Addresses assigned interface name
                if "ipam.ipaddress" in enabled_models:
                    enabled_models.append("dcim.interface")
                transform_maps = self.sync.get_transform_maps()
                for endpoint in IPFabricEndpoint.objects.all():
                    tms_for_endpoint = transform_maps.filter(source_endpoint=endpoint)
                    if not tms_for_endpoint.exists():
                        raise SyncError(
                            f"No transform map found for endpoint `{endpoint.endpoint}`."
                        )
                    if not [
                        True
                        for tm in tms_for_endpoint
                        if ".".join(tm.target_model.natural_key()) in enabled_models
                    ]:
                        logger.debug(
                            f"Skipping endpoint `{endpoint.endpoint}` as no enabled models are using it."
                        )
                        continue
                    filters = endpoint.combine_filters(sync=self.sync)
                    logger.debug(
                        f"Collecting data from endpoint: `{endpoint.endpoint}` using filter `{json.dumps(filters)}`."
                    )
                    data[endpoint.endpoint] = self.client.fetch_all(
                        url=endpoint.endpoint,
                        snapshot_id=self.settings["snapshot_id"],
                        filters=filters,
                    )
                    self.logger.log_info(
                        f"Collected {len(data[endpoint.endpoint])} items from endpoint `{endpoint.endpoint}`.",
                        obj=self.sync.snapshot_data.source,
                    )
        except Exception as e:
            self.logger.log_failure(
                f"Error collecting data from IP Fabric: {e}", obj=self.sync
            )
            raise SyncError(f"Error collecting data from IP Fabric: {e}")
        return data

    @cache
    def get_transform_map(self, app: str, model: str) -> "IPFabricTransformMap":
        """Get transform map for given app and model. Cached to improve performance."""
        return self.transform_maps.get(
            target_model__app_label=app, target_model__model=model
        )

    def create_new_data_records(
        self, app: str, model: str, data: list[dict] | dict[str, list[dict]]
    ) -> set[DataRecord]:
        """Create DataRecord objects for given app, model and data list if enabled in settings."""
        if not self.sync.parameters.get(f"{app}.{model}"):
            return set()
        if isinstance(data, dict):
            # Data is either already list or full data where we have to choose the list
            transform_map = self.get_transform_map(app=app, model=model)
            data = data.get(transform_map.source_endpoint.endpoint, [])
        return set(
            self.create_new_data_record(app=app, model=model, data=item)
            for item in data
        )

    def create_new_data_record(self, app: str, model: str, data: dict) -> DataRecord:
        """Extract only relevant source data according to transform map configuration."""
        transform_map = self.get_transform_map(app=app, model=model)
        model_string = f"{app}.{model}"
        try:
            source_data = transform_map.strip_source_data(data)
        except KeyError as err:
            raise SyncError(
                f"Missing key column {err.args[0]} in source data when preparing data for {model_string}."
            ) from err
        return DataRecord(
            model_string=model_string, data=source_data, transform_map=transform_map
        )

    def preprocess_data(self, data: dict) -> dict[str, set[DataRecord]]:
        # Set those records that can't be iterated separately
        # Others are as empty set to define order which is shown in UI progress
        records = {
            "dcim.site": self.create_new_data_records(
                app="dcim", model="site", data=data
            ),
            "dcim.manufacturer": set(),
            "dcim.devicetype": set(),
            "dcim.platform": set(),
            "dcim.devicerole": set(),
            "dcim.device": set(),
            "dcim.virtualchassis": set(),
            "dcim.interface": set(),
            "dcim.macaddress": set(),
            "dcim.inventoryitem": self.create_new_data_records(
                app="dcim",
                model="inventoryitem",
                data=data,
            ),
            "ipam.vlan": self.create_new_data_records(
                app="ipam",
                model="vlan",
                data=data,
            ),
            "ipam.vrf": self.create_new_data_records(
                app="ipam",
                model="vrf",
                data=data,
            ),
            "ipam.prefix": self.create_new_data_records(
                app="ipam",
                model="prefix",
                data=data,
            ),
            "ipam.ipaddress": set(),
        }

        if self.sync.parameters.get("dcim.virtualchassis"):
            self.logger.log_info("Preparing virtual chassis members", obj=self.sync)
            members = order_members(data.get("/technology/platforms/stack/members", []))
        else:
            members = []

        if self.sync.parameters.get("dcim.device") or self.sync.parameters.get(
            "dcim.virtualchassis"
        ):
            self.logger.log_info("Preparing devices", obj=self.sync)
            devices, virtualchassis = prepare_devices(
                data.get("/inventory/devices", []), members
            )
        else:
            # We can skip iterating over devices since we don't need stack members for the rest of the models
            devices, virtualchassis = data.get("/inventory/devices", []), []

        # We need to store primary IPs of Devices to assign them later
        # since they are not stored on Device object directly
        # TODO: This will be later replaced when we are able to sync from multiple API tables to 1 model
        device_primary_ips = {}

        for device in devices:
            if self.sync.parameters.get("dcim.manufacturer"):
                records["dcim.manufacturer"].add(
                    self.create_new_data_record(
                        app="dcim", model="manufacturer", data=device
                    )
                )
            if self.sync.parameters.get("dcim.devicetype"):
                records["dcim.devicetype"].add(
                    self.create_new_data_record(
                        app="dcim", model="devicetype", data=device
                    )
                )
            if self.sync.parameters.get("dcim.platform"):
                records["dcim.platform"].add(
                    self.create_new_data_record(
                        app="dcim", model="platform", data=device
                    )
                )
            if self.sync.parameters.get("dcim.devicerole"):
                records["dcim.devicerole"].add(
                    self.create_new_data_record(
                        app="dcim", model="devicerole", data=device
                    )
                )
            # This field is required by Device transform maps, but is set only when Device is part of VC.
            if "virtual_chassis" not in device:
                device["virtual_chassis"] = None
            if self.sync.parameters.get("dcim.device"):
                records["dcim.device"].add(
                    self.create_new_data_record(app="dcim", model="device", data=device)
                )
            device_primary_ips[device.get("sn")] = device.get("loginIp")

        records["dcim.virtualchassis"] = self.create_new_data_records(
            app="dcim", model="virtualchassis", data=virtualchassis
        )

        # `nameOriginal` is human-readable interface name hidden column in IP Fabric
        # This allows us to use it instead of the `intName`
        # But it can be customized using transform maps, so we need to use the current value
        interface_key = "nameOriginal"
        try:
            int_transform_map = self.get_transform_map(app="dcim", model="interface")
            int_name_field_map = int_transform_map.field_maps.get(target_field="name")
            interface_key = int_name_field_map.source_field
        except Exception as e:
            self.logger.log_failure(
                f"Error collecting information about transform map for interface name: {e}",
                obj=self.sync,
            )
            raise SyncError(f"Error collecting source column name for interface: {e}")

        # Store human-readable interface names to use them later for IP Addresses
        readable_int_names = {}
        if (
            self.sync.parameters.get("dcim.interface")
            or self.sync.parameters.get("dcim.macaddress")
            or self.sync.parameters.get("ipam.ipaddress")
        ):
            self.logger.log_info("Preparing Interfaces", obj=self.sync)
            for interface in data.get("/inventory/interfaces", []):
                if self.sync.parameters.get("dcim.interface"):
                    interface_record = self.create_new_data_record(
                        app="dcim", model="interface", data=interface
                    )
                    interface_record.data["loginIp"] = device_primary_ips.get(
                        interface.get("sn")
                    )
                    records["dcim.interface"].add(interface_record)
                readable_int_names[
                    f"{interface.get('sn')}_{interface.get('intName')}"
                ] = interface.get(interface_key)
                if self.sync.parameters.get("dcim.macaddress"):
                    records["dcim.macaddress"].add(
                        self.create_new_data_record(
                            app="dcim", model="macaddress", data=interface
                        )
                    )

        if self.sync.parameters.get("ipam.ipaddress"):
            self.logger.log_info("Preparing IP Addresses", obj=self.sync)
            for ip in data.get("/technology/addressing/managed-ip/ipv4", []):
                # We get `nameOriginal` from Interface table to get human-readable name instead fo `intName`
                ip["nameOriginal"] = readable_int_names.get(
                    f"{ip.get('sn')}_{ip.get('intName')}"
                )
                # Let's skip IPs we cannot assign to an interface
                if not ip["nameOriginal"]:
                    continue
                ipaddress_record = self.create_new_data_record(
                    app="ipam", model="ipaddress", data=ip
                )
                # Store whether this IP is primary for the device
                ipaddress_record.data["is_primary"] = ip.get(
                    "sn"
                ) in device_primary_ips and device_primary_ips.get(
                    ip.get("sn")
                ) == ipaddress_record.data.get(
                    "ip"
                )
                records["ipam.ipaddress"].add(ipaddress_record)

        for model_string, records_set in records.items():
            if self.settings.get(model_string) and len(records_set):
                self.logger.init_statistics(model_string, len(records_set))
                self.logger.log_info(
                    f"Prepared {len(records_set)} items for `{model_string}` to be synced.",
                    obj=self.sync,
                )

        return records

    @handle_errors
    def sync_model(
        self,
        record: DataRecord,
        stats: bool = True,
    ) -> ModelTypeVar | None:
        """Sync a single item to NetBox."""
        if not record.data:
            return None

        instance = self.get_model_or_update(record)

        # Only log when we successfully synced the item and asked for it
        if stats and instance:
            self.logger.increment_statistics(model_string=record.model_string)

        return instance

    def sync_item(
        self,
        record: DataRecord,
        cf: bool = False,
        ingestion: "IPFabricIngestion" = None,
        stats: bool = True,
    ) -> ModelTypeVar | None:
        """Sync a single item to NetBox."""
        synced_object = self.sync_model(record=record, stats=stats)
        if synced_object is None:
            return None

        if cf:
            synced_object.snapshot()
            synced_object.custom_field_data[
                "ipfabric_source"
            ] = self.sync.snapshot_data.source.pk
            if ingestion:
                synced_object.custom_field_data["ipfabric_ingestion"] = ingestion.pk
            synced_object.save()

        return synced_object

    def sync_items(
        self,
        items: set[DataRecord],
        cf: bool = False,
        ingestion: "IPFabricIngestion" = None,
        stats: bool = True,
    ) -> None:
        """Sync list of items to NetBox."""
        if not items:
            return

        model_string = (lambda record: record.model_string)(next(iter(items)))
        if not self.settings.get(model_string):
            self.logger.log_info(
                f"Did not ask to sync {model_string}s, skipping.", obj=self.sync
            )
            return

        for item in items:
            self.sync_item(item, cf, ingestion, stats)
            self.events_clearer.increment()

    @handle_errors
    def sync_devices(
        self,
        devices: set[DataRecord],
        cf: bool = False,
        ingestion: "IPFabricIngestion" = None,
    ) -> None:
        """Sync devices separately to handle resetting primary IP."""
        if not self.settings.get("dcim.device"):
            self.logger.log_info(
                "Did not ask to sync devices, skipping.", obj=self.sync
            )
            return

        for device in devices:
            device_obj: "Device | None" = self.sync_item(
                record=device, cf=cf, ingestion=ingestion
            )

            if (
                device_obj is None
                or device_obj.primary_ip4 is None
                or device.data.get("loginIp") is not None
            ):
                self.events_clearer.increment()
                continue

            # If device has primary IP assigned in NetBox, but not in IP Fabric, remove it
            try:
                connection_name = self.get_db_connection_name()
                device_obj.refresh_from_db(using=connection_name)
                device_obj.snapshot()
                device_obj.primary_ip4 = None
                device_obj.save(using=connection_name)
            except Exception as err:
                _, issue = self.create_or_get_sync_issue(
                    exception=err,
                    ingestion=self.ingestion,
                    message="Error removing primary IP current device.",
                    model_string=device.model_string,
                    data=device.data,
                )
                self.events_clearer.increment()
                raise IPAddressPrimaryRemovalError(
                    data=device.data,
                    model_string=device.model_string,
                    issue_id=issue.pk,
                ) from err
            self.events_clearer.increment()

    @handle_errors
    def sync_ipaddress(self, ip_address: DataRecord) -> "IPAddress | None":
        """Sync a single IP Address to NetBox, separated to use @handle_errors."""
        connection_name = self.get_db_connection_name()

        # First remove primary IP from the target object.
        # It cannot be done using hooks since there is no pre_clean at it fails on full_clean()
        try:
            ipv4_address = render_jinja2(
                ip_address.transform_map.field_maps.get(
                    target_field="address"
                ).template,
                {"object": ip_address.data},
            )
            other_device = (
                Device.objects.using(connection_name)
                .exclude(serial=serial(ip_address.data))
                .get(primary_ip4__address=ipv4_address)
            )
            other_device.snapshot()
            other_device.primary_ip4 = None
            other_device.save(using=connection_name)
        except Device.DoesNotExist:
            # There is no other device with this IP as primary, all good
            pass
        except Exception as err:
            # The transform maps might be changed, and we fail to resolve the template
            # Make sure this does not crash the sync and is handled gracefully
            _, issue = self.create_or_get_sync_issue(
                exception=err,
                ingestion=self.ingestion,
                message="Error removing primary IP from other device.",
                model_string=ip_address.model_string,
                data=ip_address.data,
            )
            self.events_clearer.increment()
            raise IPAddressPrimaryRemovalError(
                data=ip_address.data,
                model_string=ip_address.model_string,
                issue_id=issue.pk,
            ) from err

        ip_address_obj: "IPAddress | None" = self.sync_item(record=ip_address)
        if ip_address_obj is None or ip_address_obj.assigned_object is None:
            self.events_clearer.increment()
            return

        parent_device = ip_address_obj.assigned_object.parent_object

        # Now assign this IP as primary to the parent device, if not assigned yet or assigned to different IP
        if ip_address.data.get("is_primary") and (
            not parent_device.primary_ip4
            or parent_device.primary_ip4.pk != ip_address_obj.pk
        ):
            try:
                parent_device.snapshot()
                parent_device.primary_ip4 = ip_address_obj
                parent_device.save(using=connection_name)
            except Exception as err:
                _, issue = self.create_or_get_sync_issue(
                    exception=err,
                    ingestion=self.ingestion,
                    message="Error assigning primary IP to device.",
                    model_string=ip_address.model_string,
                    data=ip_address.data,
                )
                self.events_clearer.increment()
                raise IPAddressPrimaryAssignmentError(
                    data=ip_address.data,
                    model_string=ip_address.model_string,
                    issue_id=issue.pk,
                ) from err
        self.events_clearer.increment()

    @handle_errors
    def sync_ip_addresses(self, ip_addresses: set[DataRecord]) -> None:
        """
        We cannot assign primary IP in signals since IPAddress does not
        contain information whether it is primary or not. And it must be done
        on Device object, so cannot be done via Transform Maps yet since that
        would require another Transform Map for Device.
        So we need to do it manually here.

        Cleaning events queue happens during each cycle to make sure all required
        operations (primary IP assignment) happen during the same batch.
        """
        if not self.settings.get("ipam.ipaddress"):
            self.logger.log_info(
                "Did not ask to sync ipaddresses, skipping.", obj=self.sync
            )
            return

        for ip_address in ip_addresses:
            self.sync_ipaddress(ip_address)

    def collect_and_sync(self, ingestion=None) -> None:
        self.logger.log_info("Starting data collection.", obj=self.sync)
        data = self.collect_data()
        self.logger.log_info("Starting to prepare items.", obj=self.sync)
        records = self.preprocess_data(data=data)

        self.logger.log_info("Starting data sync.", obj=self.sync)
        try:
            # This signal does not call for snapshot(), causing issue with branching plugin
            signals.post_save.disconnect(sync_cached_scope_fields, sender=Site)
            self.sync_items(
                items=records["dcim.site"],
                cf=self.sync.update_custom_fields,
                ingestion=ingestion,
            )
        finally:
            signals.post_save.connect(sync_cached_scope_fields, sender=Site)
        self.sync_items(items=records["dcim.manufacturer"])
        self.sync_items(items=records["dcim.devicetype"])
        self.sync_items(items=records["dcim.platform"])
        self.sync_items(items=records["dcim.devicerole"])
        try:
            # This signal does not call for snapshot(), causing issue with branching plugin
            signals.post_save.disconnect(
                assign_virtualchassis_master, sender=VirtualChassis
            )
            self.sync_items(items=records["dcim.virtualchassis"])
            self.sync_devices(
                devices=records["dcim.device"],
                cf=self.sync.update_custom_fields,
                ingestion=ingestion,
            )
            # The Device exists now, so we can update the master of the VC.
            # The logic is handled in transform maps.
            self.sync_items(items=records["dcim.virtualchassis"], stats=False)
        finally:
            signals.post_save.connect(
                assign_virtualchassis_master, sender=VirtualChassis
            )
        self.sync_items(items=records["dcim.interface"])
        self.sync_items(items=records["dcim.macaddress"])
        self.sync_items(items=records["dcim.inventoryitem"])
        self.sync_items(items=records["ipam.vlan"])
        self.sync_items(items=records["ipam.vrf"])
        self.sync_items(items=records["ipam.prefix"])
        self.sync_ip_addresses(ip_addresses=records["ipam.ipaddress"])

        # Make sure to clean queue (and memory) at the end
        self.events_clearer.clear()
