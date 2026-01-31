from django.contrib.contenttypes.models import ContentType
from netbox.api.fields import ChoiceField
from netbox.api.fields import ContentTypeField
from netbox.api.fields import RelatedObjectCountField
from netbox.api.serializers import NestedGroupModelSerializer
from netbox_branching.api.serializers import BranchSerializer
from rest_framework import serializers

from ipfabric_netbox.choices import IPFabricSourceStatusChoices
from ipfabric_netbox.choices import IPFabricSyncStatusChoices
from ipfabric_netbox.models import IPFabricEndpoint
from ipfabric_netbox.models import IPFabricFilter
from ipfabric_netbox.models import IPFabricFilterExpression
from ipfabric_netbox.models import IPFabricIngestion
from ipfabric_netbox.models import IPFabricIngestionIssue
from ipfabric_netbox.models import IPFabricRelationshipField
from ipfabric_netbox.models import IPFabricRelationshipFieldSourceModels
from ipfabric_netbox.models import IPFabricSnapshot
from ipfabric_netbox.models import IPFabricSource
from ipfabric_netbox.models import IPFabricSupportedSyncModels
from ipfabric_netbox.models import IPFabricSync
from ipfabric_netbox.models import IPFabricTransformField
from ipfabric_netbox.models import IPFabricTransformMap
from ipfabric_netbox.models import IPFabricTransformMapGroup

__all__ = (
    "IPFabricEndpointSerializer",
    "IPFabricFilterSerializer",
    "IPFabricFilterExpressionSerializer",
    "IPFabricIngestionSerializer",
    "IPFabricIngestionIssueSerializer",
    "IPFabricRelationshipFieldSerializer",
    "IPFabricSnapshotSerializer",
    "IPFabricSourceSerializer",
    "IPFabricSyncSerializer",
    "IPFabricTransformFieldSerializer",
    "IPFabricTransformMapSerializer",
    "IPFabricTransformMapGroupSerializer",
)


class IPFabricEndpointSerializer(NestedGroupModelSerializer):
    class Meta:
        model = IPFabricEndpoint
        fields = (
            "id",
            "name",
            "display",
            "description",
            "endpoint",
            "created",
            "last_updated",
        )
        brief_fields = (
            "id",
            "name",
            "display",
            "endpoint",
        )


class IPFabricTransformMapGroupSerializer(NestedGroupModelSerializer):
    transform_maps_count = RelatedObjectCountField("transform_maps")

    class Meta:
        model = IPFabricTransformMapGroup
        fields = (
            "id",
            "name",
            "display",
            "description",
            "transform_maps_count",
            "created",
            "last_updated",
        )
        brief_fields = (
            "id",
            "name",
            "display",
            "description",
        )


class IPFabricTransformMapSerializer(NestedGroupModelSerializer):
    group = IPFabricTransformMapGroupSerializer(
        nested=True, required=False, allow_null=True
    )
    source_endpoint = IPFabricEndpointSerializer(nested=True, required=True)
    target_model = ContentTypeField(
        queryset=ContentType.objects.filter(IPFabricSupportedSyncModels)
    )
    parents = serializers.PrimaryKeyRelatedField(
        queryset=IPFabricTransformMap.objects.all(),
        many=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = IPFabricTransformMap
        fields = (
            "id",
            "name",
            "display",
            "group",
            "parents",
            "source_endpoint",
            "target_model",
            "created",
            "last_updated",
        )
        brief_fields = (
            "id",
            "name",
            "display",
            "group",
            "source_endpoint",
            "target_model",
        )


class IPFabricTransformFieldSerializer(NestedGroupModelSerializer):
    transform_map = IPFabricTransformMapSerializer(nested=True)

    class Meta:
        model = IPFabricTransformField
        fields = (
            "id",
            "transform_map",
            "display",
            "source_field",
            "target_field",
            "coalesce",
            "template",
        )


class IPFabricRelationshipFieldSerializer(NestedGroupModelSerializer):
    transform_map = IPFabricTransformMapSerializer(nested=True)
    source_model = ContentTypeField(
        queryset=ContentType.objects.filter(IPFabricRelationshipFieldSourceModels)
    )

    class Meta:
        model = IPFabricRelationshipField
        fields = (
            "id",
            "transform_map",
            "display",
            "source_model",
            "target_field",
            "coalesce",
            "template",
        )


class IPFabricSourceSerializer(NestedGroupModelSerializer):
    status = ChoiceField(choices=IPFabricSourceStatusChoices, read_only=True)
    url = serializers.URLField()

    class Meta:
        model = IPFabricSource
        fields = (
            "id",
            "url",
            "display",
            "name",
            "type",
            "status",
            "last_synced",
            "description",
            "comments",
            "parameters",
            "created",
            "last_updated",
        )
        brief_fields = (
            "display",
            "id",
            "name",
            "status",
            "type",
            "url",
        )


class IPFabricSnapshotSerializer(NestedGroupModelSerializer):
    source = IPFabricSourceSerializer(nested=True, read_only=True)
    data = serializers.JSONField()
    display = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = IPFabricSnapshot
        fields = (
            "id",
            "display",
            "name",
            "source",
            "snapshot_id",
            "status",
            "data",
            "date",
            "created",
            "last_updated",
        )
        brief_fields = (
            "display",
            "id",
            "name",
            "source",
            "snapshot_id",
            "status",
            "data",
            "date",
        )


class IPFabricSyncSerializer(NestedGroupModelSerializer):
    status = ChoiceField(choices=IPFabricSyncStatusChoices, read_only=True)
    snapshot_data = IPFabricSnapshotSerializer(nested=True)
    parameters = serializers.JSONField()

    class Meta:
        model = IPFabricSync
        fields = (
            "id",
            "name",
            "display",
            "snapshot_data",
            "status",
            "parameters",
            "auto_merge",
            "last_synced",
            "scheduled",
            "interval",
            "user",
            "filters",
        )
        brief_fields = (
            "auto_merge",
            "id",
            "last_synced",
            "name",
            "display",
            "parameters",
            "status",
        )


class IPFabricFilterSerializer(NestedGroupModelSerializer):
    expressions = serializers.SerializerMethodField(read_only=True)

    def get_expressions(self, obj):
        """Return the related expressions for this filter."""
        return [{"id": expr.id, "name": expr.name} for expr in obj.expressions.all()]

    class Meta:
        model = IPFabricFilter
        fields = (
            "id",
            "name",
            "display",
            "description",
            "endpoints",
            "filter_type",
            "syncs",
            "expressions",
            "created",
            "last_updated",
            "tags",
        )
        brief_fields = (
            "id",
            "name",
            "display",
            "endpoints",
            "filter_type",
            "syncs",
            "expressions",
        )


class IPFabricFilterExpressionSerializer(NestedGroupModelSerializer):
    expression = serializers.JSONField()

    class Meta:
        model = IPFabricFilterExpression
        fields = (
            "id",
            "name",
            "display",
            "description",
            "filters",
            "expression",
            "created",
            "last_updated",
            "tags",
        )
        brief_fields = (
            "id",
            "name",
            "display",
            "filters",
            "expression",
        )


class IPFabricIngestionSerializer(NestedGroupModelSerializer):
    branch = BranchSerializer(read_only=True)
    sync = IPFabricSyncSerializer(nested=True)

    class Meta:
        model = IPFabricIngestion
        fields = (
            "id",
            "name",
            "display",
            "branch",
            "sync",
        )
        brief_fields = (
            "id",
            "name",
            "display",
            "branch",
            "sync",
        )


class IPFabricIngestionIssueSerializer(NestedGroupModelSerializer):
    ingestion = IPFabricIngestionSerializer(nested=True)

    class Meta:
        model = IPFabricIngestionIssue
        fields = (
            "id",
            "ingestion",
            "display",
            "timestamp",
            "model",
            "message",
            "raw_data",
            "coalesce_fields",
            "defaults",
            "exception",
        )
        brief_fields = (
            "exception",
            "id",
            "ingestion",
            "display",
            "message",
            "model",
        )


class EmptySerializer(serializers.Serializer):
    pass
