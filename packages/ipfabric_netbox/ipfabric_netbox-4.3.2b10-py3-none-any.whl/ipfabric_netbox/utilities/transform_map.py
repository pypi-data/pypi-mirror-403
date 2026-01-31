import importlib.resources
import json
import logging
from typing import Any
from typing import Callable

from django.apps import apps as django_apps


logger = logging.getLogger("ipfabric_netbox.utilities.transform_map")

# region Transform Map Creation

# These functions are used in the migration file to prepare the transform maps
# Because of this we have to use historical models
# see https://docs.djangoproject.com/en/5.1/topics/migrations/#historical-models


def build_fields(data, apps, db_alias):
    ContentType = apps.get_model("contenttypes", "ContentType")
    if "target_model" in data:
        ct = ContentType.objects.db_manager(db_alias).get_for_model(
            apps.get_model(
                data["target_model"]["app_label"],
                data["target_model"]["model"],
            )
        )
        data["target_model"] = ct
    elif "source_model" in data:
        ct = ContentType.objects.db_manager(db_alias).get_for_model(
            apps.get_model(
                data["source_model"]["app_label"],
                data["source_model"]["model"],
            )
        )
        data["source_model"] = ct
    return data


def build_transform_maps(data, apps: django_apps = None, db_alias: str = "default"):
    apps = apps or django_apps
    ContentType = apps.get_model("contenttypes", "ContentType")
    IPFabricTransformMap = apps.get_model("ipfabric_netbox", "IPFabricTransformMap")
    IPFabricTransformField = apps.get_model("ipfabric_netbox", "IPFabricTransformField")
    IPFabricRelationshipField = apps.get_model(
        "ipfabric_netbox", "IPFabricRelationshipField"
    )

    # Mapping for backward compatibility (endpoint -> source_model)
    # Used only when running against old model that still has source_model field
    # TODO: Remove once migrations are squashed and old versions are no longer supported
    endpoint_to_source_model = {
        "/technology/addressing/managed-ip/ipv4": "ipaddress",
        "/inventory/devices": "device",
        "/inventory/sites/overview": "site",
        "/inventory/interfaces": "interface",
        "/inventory/part-numbers": "part_number",
        "/technology/vlans/site-summary": "vlan",
        "/technology/routing/vrf/detail": "vrf",
        "/technology/networks/managed-networks": "prefix",
        "/technology/platforms/stack1/members": "virtualchassis",
    }

    model_fields = {f.name for f in IPFabricTransformMap._meta.get_fields()}
    for tm in data:
        field_data = build_fields(tm["data"], apps, db_alias)

        endpoint_value = field_data.pop("source_endpoint")

        if "source_endpoint" in model_fields:
            # New model: use source_endpoint foreign key to IPFabricEndpoint
            # This models does not exist when TMs are populated, so need to get it here
            IPFabricEndpoint = apps.get_model("ipfabric_netbox", "IPFabricEndpoint")
            try:
                endpoint = IPFabricEndpoint.objects.using(db_alias).get(
                    endpoint=endpoint_value
                )
                field_data["source_endpoint"] = endpoint
            except IPFabricEndpoint.DoesNotExist:
                # Use first endpoint as fallback
                endpoint = IPFabricEndpoint.objects.using(db_alias).first()
                field_data["source_endpoint"] = endpoint
                field_data[
                    "name"
                ] = f"[NEEDS CORRECTION - Expected endpoint '{endpoint_value}' not found] {field_data['name']}"

        else:
            # Old model: convert source_endpoint value to source_model string
            source_model_value = endpoint_to_source_model.get(endpoint_value, "device")
            field_data["source_model"] = source_model_value

        # This field was not present in the old model, so remove it if exists
        tm_parents = []
        if parents := field_data.pop("parents", None):
            if isinstance(parents, str):
                parents = [parents]
            for parent in parents:
                if "parents" not in model_fields:
                    continue
                # New model: set parents MTM field to IPFabricTransformMap
                app, model = parent.split(".")
                try:
                    parent_tm = IPFabricTransformMap.objects.using(db_alias).get(
                        target_model=ContentType.objects.using(db_alias).get(
                            app_label=app, model=model
                        ),
                        group__isnull=True,
                    )
                    tm_parents.append(parent_tm)
                except IPFabricTransformMap.DoesNotExist:
                    raise ValueError(f"Parent Transform Map '{parent}' not found")

        tm_obj = IPFabricTransformMap.objects.using(db_alias).create(**field_data)
        # Old migrations may not have parents field
        if hasattr(tm_obj, "parents"):
            tm_obj.parents.set(tm_parents)
        for fm in tm["field_maps"]:
            field_data = build_fields(fm, apps, db_alias)
            IPFabricTransformField.objects.using(db_alias).create(
                transform_map=tm_obj, **field_data
            )
        for rm in tm["relationship_maps"]:
            relationship_data = build_fields(rm, apps, db_alias)
            IPFabricRelationshipField.objects.using(db_alias).create(
                transform_map=tm_obj, **relationship_data
            )


def get_transform_map() -> dict:
    for data_file in importlib.resources.files("ipfabric_netbox.data").iterdir():
        if data_file.name != "transform_map.json":
            continue
        with open(data_file, "rb") as data_file:
            return json.load(data_file)
    raise FileNotFoundError("'transform_map.json' not found in installed package")


# endregion
# region Transform Map Updating


class Record:
    """Base class for field and relationship records."""

    def __init__(
        self,
        coalesce: bool | None = None,
        old_template: str = None,
        new_template: str = None,
    ):
        self.coalesce = coalesce
        # Keep the original template here rather than loading it from transform_map.json
        # so our revert won’t break if that template ever changes.
        self.old_template = old_template
        self.new_template = new_template


class FieldRecord(Record):
    def __init__(
        self,
        source_field: str,
        target_field: str,
        new_source_field: str | None = None,
        new_target_field: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.source_field = source_field
        self.target_field = target_field
        self.new_source_field = new_source_field
        self.new_target_field = new_target_field


class RelationshipRecord(Record):
    def __init__(self, source_model: str, target_field: str, **kwargs):
        super().__init__(**kwargs)
        self.source_model = source_model
        self.target_field = target_field


class TransformMapRecord:
    def __init__(
        self,
        source_model: str,
        target_model: str,
        fields: tuple[FieldRecord, ...] = tuple(),
        relationships: tuple[RelationshipRecord, ...] = tuple(),
    ):
        self.source_model = source_model
        self.target_model = target_model
        self.fields = fields
        self.relationships = relationships


def do_change(
    apps, schema_editor, changes: tuple[TransformMapRecord, ...], forward: bool = True
):
    """Apply the changes, `forward` determines direction."""

    ContentType = apps.get_model("contenttypes", "ContentType")
    IPFabricTransformMap = apps.get_model("ipfabric_netbox", "IPFabricTransformMap")
    IPFabricTransformField = apps.get_model("ipfabric_netbox", "IPFabricTransformField")
    IPFabricRelationshipField = apps.get_model(
        "ipfabric_netbox", "IPFabricRelationshipField"
    )

    try:
        for change in changes:
            app, model = change.target_model.split(".")
            try:
                transform_map = IPFabricTransformMap.objects.get(
                    source_model=change.source_model,
                    target_model=ContentType.objects.get(app_label=app, model=model),
                )
            except IPFabricTransformMap.DoesNotExist:
                continue

            for field in change.fields:
                # Find the correct transform field.
                # Only 1 should be found if it exists, but keep it as queryset so we can filter and update.
                transform_field_qs = IPFabricTransformField.objects.filter(
                    transform_map=transform_map,
                    source_field=field.source_field
                    if forward
                    else field.new_source_field or field.source_field,
                    target_field=field.target_field
                    if forward
                    else field.new_target_field or field.target_field,
                )
                if not transform_field_qs.exists():
                    continue

                if field.old_template is not None and field.new_template is not None:
                    # First update the template if needed
                    transform_field_qs.filter(
                        template=field.old_template if forward else field.new_template
                    ).update(
                        template=field.new_template if forward else field.old_template
                    )

                if field.coalesce is not None:
                    # Next update coalesce if needed
                    transform_field_qs.filter(
                        coalesce=not field.coalesce if forward else field.coalesce
                    ).update(coalesce=field.coalesce if forward else not field.coalesce)

                if (
                    field.new_target_field is not None
                    or field.new_source_field is not None
                ):
                    # And at the end update source_field/target_field if needed
                    transform_field_qs.update(
                        source_field=field.new_source_field or field.source_field
                        if forward
                        else field.source_field,
                        target_field=field.new_target_field or field.target_field
                        if forward
                        else field.target_field,
                    )

            for relationship in change.relationships:
                s_app, s_model = relationship.source_model.split(".")
                source_model = ContentType.objects.get(app_label=s_app, model=s_model)

                # Find the correct relationship field.
                # Only 1 should be found if it exists, but keep it as queryset so we can filter and update.
                relationship_qs = IPFabricRelationshipField.objects.filter(
                    transform_map=transform_map,
                    source_model=source_model,
                    target_field=relationship.target_field,
                )
                if not relationship_qs.exists():
                    continue

                if (
                    relationship.old_template is not None
                    and relationship.new_template is not None
                ):
                    # First update the template if needed
                    relationship_qs.filter(
                        template=relationship.old_template
                        if forward
                        else relationship.new_template,
                    ).update(
                        template=relationship.new_template
                        if forward
                        else relationship.old_template
                    ),

                if relationship.coalesce is not None:
                    # Next update coalesce if needed
                    relationship_qs.filter(
                        coalesce=not relationship.coalesce
                        if forward
                        else relationship.coalesce,
                    ).update(
                        coalesce=relationship.coalesce
                        if forward
                        else not relationship.coalesce
                    ),

    except Exception as e:
        print(f"Error applying Transform map updates: {e}")


# endregion

# region Cycle Detection


def has_cycle_dfs(
    node_id: int,
    get_parents_func: Callable[[int, Any], Any],
    parent_override: Any = None,
    visited: set[int] | None = None,
    rec_stack: set[int] | None = None,
) -> bool:
    """
    DFS helper to detect cycles in transform map parent relationships.

    Args:
        node_id: The ID of the current node being checked
        get_parents_func: Function that takes (node_id, parent_override) and returns parent objects
        parent_override: Optional override for parents of a specific node (used for validation)
        visited: Set of already visited node IDs (created automatically if not provided)
        rec_stack: Set of node IDs in the current recursion stack (created automatically if not provided)

    Returns:
        True if a cycle is detected, False otherwise
    """
    if visited is None:
        visited = set()
    if rec_stack is None:
        rec_stack = set()

    visited.add(node_id)
    rec_stack.add(node_id)

    try:
        parents = get_parents_func(node_id, parent_override)

        for parent in parents:
            parent_pk = parent.pk if hasattr(parent, "pk") else parent.id
            if parent_pk not in visited:
                if has_cycle_dfs(
                    parent_pk, get_parents_func, visited=visited, rec_stack=rec_stack
                ):
                    return True
            elif parent_pk in rec_stack:
                # Found a back edge - cycle detected
                return True
    except Exception as err:
        logger.warning(f"Error applying Transform map updates: {err}")

    rec_stack.remove(node_id)
    return False


# endregion
