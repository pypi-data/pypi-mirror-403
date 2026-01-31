from typing import TYPE_CHECKING

from django.db import migrations

from ipfabric_netbox.utilities.endpoint import build_endpoints
from ipfabric_netbox.utilities.endpoint import get_endpoint_data
from ipfabric_netbox.utilities.filters import build_filters
from ipfabric_netbox.utilities.filters import get_filter_data
from ipfabric_netbox.utilities.transform_map import get_transform_map

if TYPE_CHECKING:
    from django.apps import apps as apps_type
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def prepare_endpoints(apps: "apps_type", schema_editor: "BaseDatabaseSchemaEditor"):
    """Create endpoints if they do not exist yet."""
    build_endpoints(
        data=get_endpoint_data(), apps=apps, db_alias=schema_editor.connection.alias
    )


def prepare_filters(apps: "apps_type", schema_editor: "BaseDatabaseSchemaEditor"):
    """Create filters if they do not exist yet."""
    build_filters(
        data=get_filter_data(), apps=apps, db_alias=schema_editor.connection.alias
    )


def assign_filters_to_syncs(
    apps: "apps_type", schema_editor: "BaseDatabaseSchemaEditor"
):
    """Assign all created IPFabricFilters to all existing IPFabricSync objects."""
    IPFabricSync = apps.get_model("ipfabric_netbox", "IPFabricSync")
    IPFabricFilter = apps.get_model("ipfabric_netbox", "IPFabricFilter")

    all_filters = IPFabricFilter.objects.using(schema_editor.connection.alias).all()
    for sync in IPFabricSync.objects.using(schema_editor.connection.alias).all():
        sync.filters.set(all_filters)


def migrate_source_model_to_endpoint(
    apps: "apps_type", schema_editor: "BaseDatabaseSchemaEditor"
):
    """Migrate IPFabricTransformMap source_model data to source_endpoint."""
    IPFabricTransformMap = apps.get_model("ipfabric_netbox", "IPFabricTransformMap")
    IPFabricEndpoint = apps.get_model("ipfabric_netbox", "IPFabricEndpoint")

    source_model_to_endpoint = {
        "site": "/inventory/sites/overview",
        "device": "/inventory/devices",
        "virtualchassis": "/technology/platforms/stack/members",
        "interface": "/inventory/interfaces",
        "part_number": "/inventory/part-numbers",
        "vlan": "/technology/vlans/site-summary",
        "vrf": "/technology/routing/vrf/detail",
        "prefix": "/technology/networks/managed-networks",
        "ipaddress": "/technology/addressing/managed-ip/ipv4",
        "inventory": "/inventory/part-numbers",
    }

    # Get first endpoint as fallback to make sure it's always set
    fallback_endpoint = IPFabricEndpoint.objects.using(
        schema_editor.connection.alias
    ).first()

    for transform_map in IPFabricTransformMap.objects.using(
        schema_editor.connection.alias
    ).all():
        endpoint_value = source_model_to_endpoint.get(transform_map.source_model)

        # If no mapping exists, use fallback and mark the name for manual fix
        if not endpoint_value:
            if not transform_map.name.startswith("[NEEDS CORRECTION]"):
                transform_map.name = f"[NEEDS CORRECTION - Unknown source_model: {transform_map.source_model}] {transform_map.name}"
            transform_map.source_endpoint = fallback_endpoint
            transform_map.save()
            continue

        # Try to get the mapped endpoint
        try:
            endpoint = IPFabricEndpoint.objects.using(
                schema_editor.connection.alias
            ).get(endpoint=endpoint_value)
            transform_map.source_endpoint = endpoint
        except IPFabricEndpoint.DoesNotExist:
            # Use fallback endpoint and mark the name
            if not transform_map.name.startswith("[NEEDS CORRECTION]"):
                transform_map.name = f"[NEEDS CORRECTION - Expected endpoint '{endpoint_value}' not found] {transform_map.name}"
            transform_map.source_endpoint = fallback_endpoint
        transform_map.save()


def migrate_endpoint_to_source_model(
    apps: "apps_type", schema_editor: "BaseDatabaseSchemaEditor"
):
    """Reverse migration: migrate IPFabricTransformMap source_endpoint data back to source_model."""
    IPFabricTransformMap = apps.get_model("ipfabric_netbox", "IPFabricTransformMap")
    IPFabricEndpoint = apps.get_model("ipfabric_netbox", "IPFabricEndpoint")

    endpoint_to_source_model = {
        "/inventory/sites/overview": "site",
        "/inventory/devices": "device",
        "/technology/platforms/stack/members": "virtualchassis",
        "/inventory/interfaces": "interface",
        "/inventory/part-numbers": "part_number",
        "/technology/vlans/site-summary": "vlan",
        "/technology/routing/vrf/detail": "vrf",
        "/technology/networks/managed-networks": "prefix",
        "/technology/addressing/managed-ip/ipv4": "ipaddress",
    }

    for transform_map in IPFabricTransformMap.objects.using(
        schema_editor.connection.alias
    ).all():
        if not transform_map.source_endpoint:
            continue

        # Get the endpoint and map it back to source_model
        try:
            endpoint = IPFabricEndpoint.objects.using(
                schema_editor.connection.alias
            ).get(pk=transform_map.source_endpoint_id)
            source_model_value = endpoint_to_source_model.get(endpoint.endpoint)
            transform_map.source_model = source_model_value
        except IPFabricEndpoint.DoesNotExist:
            pass

        # Restore original name by removing correction markers
        if transform_map.name.startswith("[NEEDS CORRECTION"):
            # Extract original name after the correction marker
            import re

            match = re.match(r"\[NEEDS CORRECTION[^]]*]\s*(.+)", transform_map.name)
            if match:
                transform_map.name = match.group(1)
        transform_map.save()


transform_keys = {
    "site": "dcim.site",
    "vlan": "ipam.vlan",
    "manufacturer": "dcim.manufacturer",
    "vrf": "ipam.vrf",
    "platform": "dcim.platform",
    "devicerole": "dcim.devicerole",
    "devicetype": "dcim.devicetype",
    "prefix": "ipam.prefix",
    "device": "dcim.device",
    "virtualchassis": "dcim.virtualchassis",
    "ipaddress": "ipam.ipaddress",
    "interface": "dcim.interface",
    "inventoryitem": "dcim.inventoryitem",
    "macaddress": "dcim.macaddress",
}


def correct_sync_parameters(
    apps: "apps_type", schema_editor: "BaseDatabaseSchemaEditor"
):
    """Correct existing sync parameters to match new structure."""
    IPFabricSync = apps.get_model("ipfabric_netbox", "IPFabricSync")
    for sync in IPFabricSync.objects.using(schema_editor.connection.alias).all():
        for old_key, new_key in transform_keys.items():
            if old_key not in sync.parameters:
                continue
            sync.parameters[new_key] = sync.parameters.pop(old_key)
            sync.save()


def return_sync_parameters(
    apps: "apps_type", schema_editor: "BaseDatabaseSchemaEditor"
):
    """Reverse the key renaming in sync parameters to restore original structure."""
    IPFabricSync = apps.get_model("ipfabric_netbox", "IPFabricSync")
    reverse_transform_keys = {v: k for k, v in transform_keys.items()}
    for sync in IPFabricSync.objects.using(schema_editor.connection.alias).all():
        for new_key, old_key in reverse_transform_keys.items():
            if new_key not in sync.parameters:
                continue
            sync.parameters[old_key] = sync.parameters.pop(new_key)
            sync.save()


def assign_parent_transform_maps(
    apps: "apps_type", schema_editor: "BaseDatabaseSchemaEditor"
):
    """Assign parent relationships to transform maps based on transform_map.json data."""

    IPFabricTransformMap = apps.get_model("ipfabric_netbox", "IPFabricTransformMap")
    ContentType = apps.get_model("contenttypes", "ContentType")
    transform_map_data = get_transform_map()

    # Process each transform map from JSON
    for tm_data in transform_map_data:
        data = tm_data.get("data", {})

        parents_value = data.get("parents")
        if not parents_value:
            continue

        # Handle both string (single parent) and array (multiple parents) formats
        if isinstance(parents_value, str):
            parents_value = [parents_value]

        try:
            # Find the transform map (without group) matching this target model
            target_model_data = data.get("target_model", {})
            target_model = ContentType.objects.using(
                schema_editor.connection.alias
            ).get(
                app_label=target_model_data.get("app_label"),
                model=target_model_data.get("model"),
            )
            transform_map = (
                IPFabricTransformMap.objects.using(schema_editor.connection.alias)
                .filter(group__isnull=True, target_model=target_model)
                .first()
            )
            if not transform_map:
                continue

            # Add each parent to the M2M relationship
            for parent_str in parents_value:
                parent_app_label, parent_model = parent_str.split(".")

                try:
                    parent_content_type = ContentType.objects.using(
                        schema_editor.connection.alias
                    ).get(app_label=parent_app_label, model=parent_model)
                    parent_transform_map = (
                        IPFabricTransformMap.objects.using(
                            schema_editor.connection.alias
                        )
                        .filter(group__isnull=True, target_model=parent_content_type)
                        .first()
                    )
                    if parent_transform_map:
                        transform_map.parents.add(parent_transform_map)

                except ContentType.DoesNotExist:
                    continue

        except ContentType.DoesNotExist:
            continue


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0132_configcontextprofile"),
        ("ipfabric_netbox", "0022_prepare_for_filters"),
    ]

    operations = [
        migrations.RunPython(
            prepare_endpoints,
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            prepare_filters,
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            assign_filters_to_syncs,
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            migrate_source_model_to_endpoint,
            migrate_endpoint_to_source_model,
        ),
        migrations.RunPython(
            correct_sync_parameters,
            return_sync_parameters,
        ),
        migrations.RunPython(
            assign_parent_transform_maps,
            migrations.RunPython.noop,
        ),
    ]
