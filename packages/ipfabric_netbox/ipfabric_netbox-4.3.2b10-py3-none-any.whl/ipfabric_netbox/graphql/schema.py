import strawberry
import strawberry_django

from .types import IPFabricDataType
from .types import IPFabricEndpointType
from .types import IPFabricFilterExpressionType
from .types import IPFabricFilterType
from .types import IPFabricIngestionIssueType
from .types import IPFabricIngestionType
from .types import IPFabricRelationshipFieldType
from .types import IPFabricSnapshotType
from .types import IPFabricSourceType
from .types import IPFabricSyncType
from .types import IPFabricTransformFieldType
from .types import IPFabricTransformMapGroupType
from .types import IPFabricTransformMapType


__all__ = (
    "IPFabricTransformMapGroupQuery",
    "IPFabricTransformMapQuery",
    "IPFabricSyncQuery",
    "IPFabricTransformFieldQuery",
    "IPFabricRelationshipFieldQuery",
    "IPFabricSourceQuery",
    "IPFabricSnapshotQuery",
    "IPFabricIngestionQuery",
    "IPFabricIngestionIssueQuery",
    "IPFabricDataQuery",
    "IPFabricEndpointQuery",
    "IPFabricFilterQuery",
    "IPFabricFilterExpressionQuery",
)


@strawberry.type(name="Query")
class IPFabricTransformMapGroupQuery:
    ipfabric_transform_map_group: IPFabricTransformMapGroupType = (
        strawberry_django.field()
    )
    ipfabric_transform_map_group_list: list[
        IPFabricTransformMapGroupType
    ] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricTransformMapQuery:
    ipfabric_transform_map: IPFabricTransformMapType = strawberry_django.field()
    ipfabric_transform_map_list: list[
        IPFabricTransformMapType
    ] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricTransformFieldQuery:
    ipfabric_transform_field: IPFabricTransformFieldType = strawberry_django.field()
    ipfabric_transform_field_list: list[
        IPFabricTransformFieldType
    ] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricRelationshipFieldQuery:
    ipfabric_relationship_field: IPFabricRelationshipFieldType = (
        strawberry_django.field()
    )
    ipfabric_relationship_field_list: list[
        IPFabricRelationshipFieldType
    ] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricSourceQuery:
    ipfabric_source: IPFabricSourceType = strawberry_django.field()
    ipfabric_source_list: list[IPFabricSourceType] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricSnapshotQuery:
    ipfabric_snapshot: IPFabricSnapshotType = strawberry_django.field()
    ipfabric_snapshot_list: list[IPFabricSnapshotType] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricSyncQuery:
    ipfabric_sync: IPFabricSyncType = strawberry_django.field()
    ipfabric_sync_list: list[IPFabricSyncType] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricIngestionQuery:
    ipfabric_ingestion: IPFabricIngestionType = strawberry_django.field()
    ipfabric_ingestion_list: list[IPFabricIngestionType] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricIngestionIssueQuery:
    ipfabric_ingestion_issue: IPFabricIngestionIssueType = strawberry_django.field()
    ipfabric_ingestion_issue_list: list[
        IPFabricIngestionIssueType
    ] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricDataQuery:
    ipfabric_data: IPFabricDataType = strawberry_django.field()
    ipfabric_data_list: list[IPFabricDataType] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricEndpointQuery:
    ipfabric_endpoint: IPFabricEndpointType = strawberry_django.field()
    ipfabric_endpoint_list: list[IPFabricEndpointType] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricFilterQuery:
    ip_fabric_filter: IPFabricFilterType = strawberry_django.field()
    ip_fabric_filter_list: list[IPFabricFilterType] = strawberry_django.field()


@strawberry.type(name="Query")
class IPFabricFilterExpressionQuery:
    ip_fabric_filter_expression: IPFabricFilterExpressionType = (
        strawberry_django.field()
    )
    ip_fabric_filter_expression_list: list[
        IPFabricFilterExpressionType
    ] = strawberry_django.field()
