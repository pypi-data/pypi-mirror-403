import strawberry
from core.choices import JobStatusChoices
from netbox_branching.choices import BranchStatusChoices

from ipfabric_netbox.choices import IPFabricFilterTypeChoices
from ipfabric_netbox.choices import IPFabricRawDataTypeChoices
from ipfabric_netbox.choices import IPFabricSnapshotStatusModelChoices
from ipfabric_netbox.choices import IPFabricSourceStatusChoices
from ipfabric_netbox.choices import IPFabricSourceTypeChoices
from ipfabric_netbox.choices import IPFabricSyncStatusChoices

__all__ = (
    "IPFabricSourceStatusEnum",
    "IPFabricSyncStatusEnum",
    "IPFabricSourceTypeEnum",
    "IPFabricSnapshotStatusModelEnum",
    "IPFabricRawDataTypeEnum",
    "BranchStatusEnum",
    "JobStatusEnum",
    "IPFabricFilterTypeEnum",
)

IPFabricSourceStatusEnum = strawberry.enum(
    IPFabricSourceStatusChoices.as_enum(prefix="type")
)
IPFabricSyncStatusEnum = strawberry.enum(
    IPFabricSyncStatusChoices.as_enum(prefix="type")
)
IPFabricSourceTypeEnum = strawberry.enum(
    IPFabricSourceTypeChoices.as_enum(prefix="type")
)
IPFabricSnapshotStatusModelEnum = strawberry.enum(
    IPFabricSnapshotStatusModelChoices.as_enum(prefix="type")
)
IPFabricRawDataTypeEnum = strawberry.enum(
    IPFabricRawDataTypeChoices.as_enum(prefix="type")
)
BranchStatusEnum = strawberry.enum(BranchStatusChoices.as_enum(prefix="type"))
JobStatusEnum = strawberry.enum(JobStatusChoices.as_enum(prefix="type"))
IPFabricFilterTypeEnum = strawberry.enum(
    IPFabricFilterTypeChoices.as_enum(prefix="type")
)
