import django_tables2 as tables
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_tables2 import Column
from netbox.tables import columns
from netbox.tables import NetBoxTable
from netbox_branching.models import ChangeDiff

from .models import IPFabricData
from .models import IPFabricEndpoint
from .models import IPFabricFilter
from .models import IPFabricFilterExpression
from .models import IPFabricIngestion
from .models import IPFabricIngestionIssue
from .models import IPFabricRelationshipField
from .models import IPFabricSnapshot
from .models import IPFabricSource
from .models import IPFabricSync
from .models import IPFabricTransformField
from .models import IPFabricTransformMap
from .models import IPFabricTransformMapGroup


DIFF_BUTTON = """
    <a href="#"
          hx-get="{% url 'plugins:ipfabric_netbox:ipfabricingestion_change_diff' pk=record.branch.pk change_pk=record.pk %}"
          hx-target="#htmx-modal-content"
          data-bs-toggle="modal"
          data-bs-target="#htmx-modal"
          class="btn btn-success btn-sm"
        >
        <i class="mdi mdi-code-tags">Diff</i>
    </a>
"""

DATA_BUTTON = """
    <a href="#"
          hx-get="{% url 'plugins:ipfabric_netbox:ipfabricdata_data' pk=record.pk %}"
          hx-target="#htmx-modal-content"
          data-bs-toggle="modal"
          data-bs-target="#htmx-modal"
          class="btn btn-success btn-sm"
        >
        <i class="mdi mdi-code-tags">JSON</i>
    </a>
"""

COMBINED_EXPRESSIONS_BUTTON = """
    <a href="#"
          hx-get="{% url 'plugins:ipfabric_netbox:ipfabricfilter_combined_expressions' pk=record.pk %}"
          hx-target="#htmx-modal-content"
          data-bs-toggle="modal"
          data-bs-target="#htmx-modal"
          class="btn btn-success btn-sm"
        >
        Combined
    </a>
"""

ENDPOINT_FILTERS_BUTTON = """
    {% if record.sync_pk %}
        <a href="#"
              hx-get="{% url 'plugins:ipfabric_netbox:ipfabricendpoint_filters' pk=record.pk %}?sync_pk={{ record.sync_pk }}&from_sync=true"
              hx-target="#htmx-modal-content"
              data-bs-toggle="modal"
              data-bs-target="#htmx-modal"
              class="btn btn-success btn-sm"
            >
            Show Filters
        </a>
    {% else %}
        <a href="#"
              hx-get="{% url 'plugins:ipfabric_netbox:ipfabricendpoint_filters' pk=record.pk %}"
              hx-target="#htmx-modal-content"
              data-bs-toggle="modal"
              data-bs-target="#htmx-modal"
              class="btn btn-success btn-sm"
            >
            Show Filters
        </a>
    {% endif %}
"""


class IPFabricEndpointTable(NetBoxTable):
    name = tables.Column(linkify=True)
    endpoint = tables.Column(verbose_name=_("Endpoint"))
    filters_count = tables.Column(
        verbose_name=_("Filters"),
        empty_values=(),
        default="",
        linkify=lambda record: f"/plugins/ipfabric/filter/?endpoint_id={record.pk}",
    )
    show_filters = columns.TemplateColumn(
        template_code=ENDPOINT_FILTERS_BUTTON,
        orderable=False,
        verbose_name=_("Combined Filters"),
        empty_values=(),
        default="",
    )
    actions = None

    def render_filters_count(self, record):
        """Only render filter count if it's available."""
        if not hasattr(record, "filters_count"):
            return ""
        return record.filters_count

    class Meta(NetBoxTable.Meta):
        model = IPFabricEndpoint
        fields = ("name", "description", "endpoint", "filters_count", "show_filters")
        default_columns = (
            "name",
            "description",
            "endpoint",
            "filters_count",
            "show_filters",
        )


class IPFabricRelationshipFieldTable(NetBoxTable):
    id = tables.Column()
    transform_map = tables.Column(linkify=True)
    source_model = columns.ContentTypeColumn(verbose_name=_("Source Model"))
    actions = columns.ActionsColumn(actions=("edit", "delete"))

    class Meta(NetBoxTable.Meta):
        model = IPFabricRelationshipField
        fields = (
            "id",
            "transform_map",
            "source_model",
            "target_field",
            "coalesce",
            "actions",
        )
        default_columns = (
            "transform_map",
            "source_model",
            "target_field",
            "coalesce",
            "actions",
        )


class IPFabricTransformFieldTable(NetBoxTable):
    id = tables.Column()
    transform_map = tables.Column(linkify=True)
    actions = columns.ActionsColumn(actions=("edit", "delete"))

    class Meta(NetBoxTable.Meta):
        model = IPFabricTransformField
        fields = (
            "id",
            "transform_map",
            "source_field",
            "target_field",
            "coalesce",
            "actions",
        )
        default_columns = (
            "transform_map",
            "source_field",
            "target_field",
            "coalesce",
            "actions",
        )


class IPFabricTransformMapGroupTable(NetBoxTable):
    name = tables.Column(linkify=True)
    maps_count = columns.LinkedCountColumn(
        viewname="plugins:ipfabric_netbox:ipfabrictransformmap_list",
        url_params={"group_id": "pk"},
        verbose_name=_("Transform Maps"),
    )

    class Meta(NetBoxTable.Meta):
        model = IPFabricTransformMapGroup
        fields = ("name", "description", "maps_count")
        default_columns = ("name", "description", "maps_count")


class IPFabricTransformMapTable(NetBoxTable):
    name = tables.Column(linkify=True)
    parents = tables.Column(linkify=False, verbose_name=_("Hierarchical Parents"))
    group = tables.Column(linkify=True)
    source_endpoint = tables.Column(linkify=True)
    target_model = columns.ContentTypeColumn(verbose_name=_("Target Model"))

    def render_parents(self, record):
        """Render multiple parents as comma-separated list with links."""
        parents = record.parents.all()
        if not parents.exists():
            return "---"

        parent_links = []
        for parent in parents:
            url = parent.get_absolute_url()
            parent_links.append(format_html('<a href="{}">{}</a>', url, parent.name))

        # Join the SafeStrings directly
        return format_html(", ".join(str(link) for link in parent_links))

    def order_parents(self, queryset, is_descending):
        """Order by count of parents."""

        queryset = queryset.annotate(parent_count=Count("parents"))

        if is_descending:
            queryset = queryset.order_by("-parent_count")
        else:
            queryset = queryset.order_by("parent_count")

        return queryset, True

    class Meta(NetBoxTable.Meta):
        model = IPFabricTransformMap
        fields = ("name", "parents", "group", "source_endpoint", "target_model")
        default_columns = (
            "name",
            "parents",
            "group",
            "source_endpoint",
            "target_model",
        )


class IPFabricIngestionTable(NetBoxTable):
    name = tables.Column(linkify=True, order_by=("branch_name", "sync_name", "id"))
    sync = tables.Column(verbose_name=_("IP Fabric Sync"), linkify=True)
    branch = tables.Column(linkify=True)
    changes = tables.Column(
        accessor="staged_changes", verbose_name=_("Number of Changes")
    )
    actions = columns.ActionsColumn(actions=("delete",))

    def render_name(self, record):
        if getattr(record, "branch_name", None):
            return record.branch_name
        elif getattr(record, "sync_name", None):
            return f"{record.sync_name} (Ingestion {record.pk})"
        else:
            return f"Ingestion {record.pk} (No Sync)"

    class Meta(NetBoxTable.Meta):
        model = IPFabricIngestion
        fields = ("name", "sync", "branch", "user", "changes")
        default_columns = ("name", "sync", "branch", "user", "changes")


class IPFabricSnapshotTable(NetBoxTable):
    name = tables.Column(linkify=True)
    source = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name="core:datasource_list")
    actions = columns.ActionsColumn(actions=("delete",))
    status = columns.ChoiceFieldColumn()

    class Meta(NetBoxTable.Meta):
        model = IPFabricSnapshot
        fields = (
            "pk",
            "id",
            "name",
            "snapshot_id",
            "status",
            "date",
            "created",
            "last_updated",
        )
        default_columns = ("pk", "name", "source", "snapshot_id", "status", "date")


class IPFabricSourceTable(NetBoxTable):
    name = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn()
    snapshot_count = tables.Column(verbose_name=_("Snapshots"))
    tags = columns.TagColumn(url_name="core:datasource_list")

    class Meta(NetBoxTable.Meta):
        model = IPFabricSource
        fields = (
            "pk",
            "id",
            "name",
            "status",
            "description",
            "comments",
            "created",
            "last_updated",
        )
        default_columns = ("pk", "name", "status", "description", "snapshot_count")


class IPFabricSyncTable(NetBoxTable):
    name = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn()
    snapshot_name = tables.Column(
        verbose_name=_("Snapshot Name"),
        accessor="snapshot_data",
        linkify=True,
    )
    last_ingestion = tables.Column(
        accessor="last_ingestion",
        verbose_name=_("Last Ingestion"),
        linkify=True,
        order_by="last_ingestion_pk",
    )

    def render_last_ingestion(self, value: IPFabricIngestion):
        return getattr(value, "name", "---") if value else "---"

    def render_snapshot_name(self, value: IPFabricSnapshot):
        return getattr(value, "name", "---") if value else "---"

    class Meta(NetBoxTable.Meta):
        model = IPFabricSync
        fields = (
            "auto_merge",
            "id",
            "interval",
            "last_synced",
            "last_ingestion",
            "name",
            "scheduled",
            "status",
            "snapshot_name",
            "user",
        )
        default_columns = ("name", "status", "last_ingestion", "snapshot_name")


class IPFabricIngestionChangesTable(NetBoxTable):
    # There is no view for single change, remove the link in ID
    id = tables.Column(verbose_name=_("ID"))
    pk = None
    object_type = tables.Column(
        accessor="object_type.model", verbose_name=_("Object Type")
    )
    object = tables.Column(verbose_name=_("Object"), order_by="object_repr")
    actions = None
    diffs = columns.TemplateColumn(template_code=DIFF_BUTTON, orderable=False)

    def render_object(self, value, record):
        model_templates = {
            "Device": lambda v: v.name,
            "DeviceRole": lambda v: v.name,
            "DeviceType": lambda v: v.model,
            "IPAddress": lambda v: v.address,
            "Interface": lambda v: f"{v.name} (Device {v.device.name})",
            "InventoryItem": lambda v: f"{v.name} (Device {v.device.name})",
            "MACAddress": lambda v: v.mac_address,
            "Manufacturer": lambda v: v.name,
            "Platform": lambda v: v.name,
            "Prefix": lambda v: f"{v.prefix} (VRF {v.vrf})",
            "Site": lambda v: v.name,
            "VirtualChassis": lambda v: v.name,
            "VLAN": lambda v: f"{v.name} (VID {v.vid})",
            "VRF": lambda v: v.name,
        }
        if value and (class_name := value.__class__.__name__) in model_templates:
            field_value = model_templates[class_name](value)
            if url := value.get_absolute_url():
                return format_html("<a href='{}'>{}</a>", url, field_value)
        else:
            field_value = record.object_repr
        return field_value

    class Meta(NetBoxTable.Meta):
        model = ChangeDiff
        name = "staged_changes"
        fields = ("object", "action", "object_type", "diffs")
        default_columns = ("object", "action", "object_type", "diffs")


class IPFabricIngestionIssuesTable(NetBoxTable):
    id = tables.Column(verbose_name=_("ID"))
    exception = tables.Column(verbose_name=_("Exception Type"))
    message = tables.Column(verbose_name=_("Error Message"))
    actions = None

    class Meta(NetBoxTable.Meta):
        model = IPFabricIngestionIssue
        fields = (
            "model",
            "timestamp",
            "raw_data",
            "coalesce_fields",
            "defaults",
            "exception",
            "message",
        )
        default_columns = ("model", "exception", "message")
        empty_text = _("No Ingestion Issues found")
        order_by = "id"


class IPFabricFilterTable(NetBoxTable):
    name = tables.Column(linkify=True)
    endpoints = tables.ManyToManyColumn(linkify_item=True)
    filter_type = columns.ChoiceFieldColumn(verbose_name=_("Filter Type"))
    syncs = tables.ManyToManyColumn(linkify_item=True)
    expressions = columns.ManyToManyColumn(
        linkify_item=True, verbose_name=_("Filter Expressions")
    )
    combined = columns.TemplateColumn(
        template_code=COMBINED_EXPRESSIONS_BUTTON,
        orderable=False,
        verbose_name=_("Combined"),
    )

    class Meta(NetBoxTable.Meta):
        model = IPFabricFilter
        fields = (
            "name",
            "description",
            "endpoints",
            "filter_type",
            "syncs",
            "expressions",
            "combined",
        )
        default_columns = (
            "name",
            "endpoints",
            "filter_type",
            "syncs",
            "expressions",
            "combined",
        )


class IPFabricFilterExpressionTable(NetBoxTable):
    name = tables.Column(linkify=True)
    expression = tables.Column(verbose_name=_("Filter Expression"))
    filters = tables.ManyToManyColumn(linkify_item=True)

    class Meta(NetBoxTable.Meta):
        model = IPFabricFilterExpression
        fields = ("name", "description", "filters", "expression")
        default_columns = ("name", "filters", "expression")


class DeviceIPFTable(tables.Table):
    hostname = Column()

    class Meta:
        attrs = {
            "class": "table table-hover object-list",
        }
        empty_text = _("No results found")

    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)


class IPFabricDataTable(NetBoxTable):
    JSON = columns.TemplateColumn(template_code=DATA_BUTTON)
    actions = columns.ActionsColumn(actions=("delete",))

    class Meta(NetBoxTable.Meta):
        model = IPFabricData
        fields = ("snapshot_data", "JSON")
        default_columns = ("snapshot_data", "JSON")
