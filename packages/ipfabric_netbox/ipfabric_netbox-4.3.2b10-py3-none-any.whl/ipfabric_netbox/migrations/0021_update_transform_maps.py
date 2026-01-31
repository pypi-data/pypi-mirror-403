from django.db import migrations

from ipfabric_netbox.utilities.transform_map import do_change
from ipfabric_netbox.utilities.transform_map import FieldRecord
from ipfabric_netbox.utilities.transform_map import RelationshipRecord
from ipfabric_netbox.utilities.transform_map import TransformMapRecord


CHANGES = (
    TransformMapRecord(
        source_model="ipaddress",
        target_model="ipam.ipaddress",
        relationships=(
            RelationshipRecord(
                source_model="ipam.vrf",
                target_field="vrf",
                coalesce=True,
                old_template='{% if object.vrf is defined and object.vrf | string not in ["", "system", "0"] %}{{ ipam.VRF.objects.filter(name=object.vrf).first().pk }}{% else %}None{% endif %}',
                new_template='{% if object.vrf is defined and object.vrf | string not in ["", "system", "0", "global"] %}{{ ipam.VRF.objects.filter(name=object.vrf).first().pk }}{% else %}None{% endif %}',
            ),
        ),
    ),
    TransformMapRecord(
        source_model="device",
        target_model="dcim.device",
        fields=(
            FieldRecord(
                source_field="hostname",
                target_field="vc_position",
                old_template="{% if object.virtual_chassis is defined %}{{ object.virtual_chassis.member }}{% else %}None{% endif %}",
                new_template="{% if object.virtual_chassis %}{{ object.virtual_chassis.member }}{% else %}None{% endif %}",
            ),
        ),
        relationships=(
            RelationshipRecord(
                source_model="dcim.virtualchassis",
                target_field="virtual_chassis",
                old_template="{% if object.virtual_chassis is defined %}{{ dcim.VirtualChassis.objects.filter(name=object.virtual_chassis.master).first().pk }}{% endif %}",
                new_template="{% if object.virtual_chassis %}{{ dcim.VirtualChassis.objects.filter(name=object.virtual_chassis.master).first().pk }}{% endif %}",
            ),
        ),
    ),
    TransformMapRecord(
        source_model="interface",
        target_model="dcim.interface",
        fields=(
            FieldRecord(
                source_field="primaryIp",
                target_field="mgmt_only",
                old_template="{% if object.primaryIp == object.loginIp %}True{% else %}False{% endif %}",
                new_template="{% if object.primaryIp and object.primaryIp == object.loginIp %}True{% else %}False{% endif %}",
            ),
        ),
    ),
    TransformMapRecord(
        source_model="interface",
        target_model="dcim.macaddress",
        fields=(
            FieldRecord(
                source_field="id",
                new_source_field="sn",
                target_field="assigned_object_id",
                old_template="",
                new_template="{% if object.nameOriginal %}{{ dcim.Interface.objects.filter(device__serial=object.sn, name=object.nameOriginal).first().pk }}{% else %}{{ dcim.Interface.objects.filter(device__serial=object.sn, name=object.intName).first().pk }}{% endif %}",
            ),
        ),
    ),
    TransformMapRecord(
        source_model="part_number",
        target_model="dcim.inventoryitem",
        fields=(
            FieldRecord(
                source_field="name",
                target_field="name",
                coalesce=True,
            ),
        ),
        relationships=(
            RelationshipRecord(
                source_model="dcim.device",
                target_field="device",
                coalesce=True,
            ),
        ),
    ),
    TransformMapRecord(
        source_model="vlan",
        target_model="ipam.vlan",
        fields=(
            FieldRecord(
                source_field="vlanName",
                target_field="name",
                old_template='{% if object.vlanName is defined and object.vlanName | lower != "none" %}{{ object.vlanName | string | truncate(64, True) }}{% else %}""{% endif %}',
                new_template='{% if object.vlanName is defined and object.vlanName | lower not in ["none", ""] %}{{ object.vlanName | string | truncate(64, True) }}{% else %}""{% endif %}',
            ),
        ),
    ),
    TransformMapRecord(
        source_model="prefix",
        target_model="ipam.prefix",
        relationships=(
            RelationshipRecord(
                source_model="ipam.vrf",
                target_field="vrf",
                old_template='{% if object.vrf is defined and object.vrf | string not in ["", "system", "0"] %}{{ ipam.VRF.objects.filter(name=object.vrf).first().pk }}{% else %}None{% endif %}',
                new_template='{% if object.vrf is defined and object.vrf | string not in ["", "system", "0", "global"] %}{{ ipam.VRF.objects.filter(name=object.vrf).first().pk }}{% else %}None{% endif %}',
            ),
        ),
    ),
)


def forward_change(apps, schema_editor):
    """Replace old template with updated version."""
    do_change(apps, schema_editor, changes=CHANGES, forward=True)


def revert_change(apps, schema_editor):
    """Revert template back to the previous exact template."""
    do_change(apps, schema_editor, changes=CHANGES, forward=False)


class Migration(migrations.Migration):
    dependencies = [
        ("ipfabric_netbox", "0020_clean_scheduled_jobs"),
    ]

    operations = [
        migrations.RunPython(
            forward_change,
            revert_change,
        ),
    ]
