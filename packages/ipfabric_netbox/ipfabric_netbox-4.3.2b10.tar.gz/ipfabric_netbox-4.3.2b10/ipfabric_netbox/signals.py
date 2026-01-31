import logging

from dcim.models import Interface
from dcim.models import MACAddress
from netbox_branching.contextvars import active_branch

logger = logging.getLogger("ipfabric_netbox.utilities.ipf_utils")


def assign_primary_mac_address(instance: MACAddress, **kwargs) -> None:
    try:
        if instance.assigned_object and instance.assigned_object.primary_mac_address:
            # The Interface already has primary MAC, nothing to do
            return
    except Interface.DoesNotExist:
        # The Interface is not created yet, cannot be assigned
        return

    connection_name = None
    if branch := active_branch.get():
        connection_name = branch.connection_name
    instance.assigned_object.snapshot()
    instance.assigned_object.primary_mac_address = instance
    instance.assigned_object.save(using=connection_name)


def remove_group_from_syncs(instance, **kwargs):
    """
    When an IPFabricTransformMapGroup is deleted, remove its ID from any IPFabricSync.parameters['groups'] list.
    """
    from ipfabric_netbox.models import IPFabricSync

    group_id = instance.pk
    for sync in IPFabricSync.objects.all():
        params = sync.parameters or {}
        groups = params.get("groups", [])
        if group_id not in groups:
            continue
        params["groups"] = [gid for gid in groups if gid != group_id]
        sync.parameters = params
        sync.save()
