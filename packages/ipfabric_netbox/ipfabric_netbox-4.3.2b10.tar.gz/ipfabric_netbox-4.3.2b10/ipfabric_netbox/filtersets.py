import django_filters
from core.choices import ObjectChangeActionChoices
from django.contrib.contenttypes.models import ContentType
from django.db.models import JSONField
from django.db.models import Q
from django.utils.translation import gettext as _
from netbox.filtersets import BaseFilterSet
from netbox.filtersets import ChangeLoggedModelFilterSet
from netbox.filtersets import NetBoxModelFilterSet
from netbox_branching.models import ChangeDiff

from .choices import IPFabricSourceStatusChoices
from .choices import IPFabricSyncStatusChoices
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


class IPFabricIngestionChangeFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search")
    action = django_filters.MultipleChoiceFilter(choices=ObjectChangeActionChoices)

    class Meta:
        model = ChangeDiff
        fields = ["branch", "action", "object_type"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(current__icontains=value)
            | Q(modified__icontains=value)
            | Q(original__icontains=value)
            | Q(action__icontains=value)
            | Q(object_type__model__icontains=value)
        )


class IPFabricIngestionIssueFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search")

    class Meta:
        model = IPFabricIngestionIssue
        fields = [
            "model",
            "timestamp",
            "raw_data",
            "coalesce_fields",
            "defaults",
            "exception",
            "message",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(model__icontains=value)
            | Q(timestamp__icontains=value)
            | Q(raw_data__icontains=value)
            | Q(coalesce_fields__icontains=value)
            | Q(defaults__icontains=value)
            | Q(exception__icontains=value)
            | Q(message__icontains=value)
        )


class IPFabricDataFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search")

    class Meta:
        model = IPFabricData
        fields = ["snapshot_data"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        # Search by snapshot name since snapshot_data is a ForeignKey
        return queryset.filter(Q(snapshot_data__name__icontains=value))


class IPFabricSnapshotFilterSet(ChangeLoggedModelFilterSet):
    q = django_filters.CharFilter(method="search")
    source_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricSource.objects.all(),
        label=_("Source (ID)"),
    )
    source = django_filters.ModelMultipleChoiceFilter(
        field_name="source__name",
        queryset=IPFabricSource.objects.all(),
        to_field_name="name",
        label=_("Source (name)"),
    )
    snapshot_id = django_filters.CharFilter(
        label=_("Snapshot ID"), lookup_expr="icontains"
    )

    class Meta:
        model = IPFabricSnapshot
        fields = ("id", "name", "status", "snapshot_id")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(name__icontains=value))


class IPFabricSourceFilterSet(NetBoxModelFilterSet):
    status = django_filters.MultipleChoiceFilter(
        choices=IPFabricSourceStatusChoices, null_value=None
    )

    class Meta:
        model = IPFabricSource
        fields = ("id", "name")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(comments__icontains=value)
        )


class IPFabricSyncFilterSet(ChangeLoggedModelFilterSet):
    q = django_filters.CharFilter(method="search")
    name = django_filters.CharFilter()
    snapshot_data_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricSnapshot.objects.all(),
        label=_("Snapshot (ID)"),
    )
    snapshot_data = django_filters.ModelMultipleChoiceFilter(
        field_name="snapshot_data__name",
        queryset=IPFabricSnapshot.objects.all(),
        to_field_name="name",
        label=_("Snapshot (name)"),
    )
    status = django_filters.MultipleChoiceFilter(
        choices=IPFabricSyncStatusChoices, null_value=None
    )

    ipfabric_filter_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricFilter.objects.all(),
        field_name="filters",
        label=_("IP Fabric Filter (ID)"),
    )
    ipfabric_filter = django_filters.CharFilter(
        field_name="filters__name",
        lookup_expr="iexact",
        label=_("IP Fabric Filter (name)"),
        distinct=True,
    )
    ipfabric_filters = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricFilter.objects.all(),
        field_name="filters",
        label=_("IP Fabric Filters"),
    )

    class Meta:
        model = IPFabricSync
        fields = (
            "id",
            "name",
            "snapshot_data",
            "snapshot_data_id",
            "status",
            "auto_merge",
            "last_synced",
            "scheduled",
            "interval",
            "ipfabric_filter_id",
            "ipfabric_filter",
            "ipfabric_filters",
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(snapshot_data__name__icontains=value)
        )


class IPFabricIngestionFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search")
    sync_id = django_filters.ModelMultipleChoiceFilter(
        field_name="sync",
        queryset=IPFabricSync.objects.all(),
        label=_("Sync (ID)"),
    )
    sync = django_filters.ModelMultipleChoiceFilter(
        field_name="sync__name",
        queryset=IPFabricSync.objects.all(),
        to_field_name="name",
        label=_("Sync (name)"),
    )

    class Meta:
        model = IPFabricIngestion
        fields = ("id", "branch", "sync")

    def search(self, queryset, branch, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(branch__name__icontains=value) | Q(sync__name__icontains=value)
        )


class IPFabricFilterFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search")

    sync_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricSync.objects.all(),
        field_name="syncs",
        label=_("Syncs (ID)"),
    )
    sync = django_filters.CharFilter(
        field_name="syncs__name",
        lookup_expr="iexact",
        label=_("Sync (name)"),
        distinct=True,
    )
    syncs = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricSync.objects.all(),
        field_name="syncs",
        label=_("Syncs (ID)"),
    )

    endpoint_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricEndpoint.objects.all(),
        field_name="endpoints",
        label=_("Endpoints (ID)"),
    )
    endpoint = django_filters.CharFilter(
        field_name="endpoints__name",
        lookup_expr="iexact",
        label=_("Endpoint (Name)"),
        distinct=True,
    )
    endpoint_path = django_filters.CharFilter(
        field_name="endpoints__endpoint",
        lookup_expr="iexact",
        label=_("Endpoint (Path)"),
        distinct=True,
    )
    endpoints = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricEndpoint.objects.all(),
        field_name="endpoints",
        label=_("Endpoints (ID)"),
    )

    expression_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricFilterExpression.objects.all(),
        field_name="expressions",
        label=_("Expression (ID)"),
    )
    expression = django_filters.CharFilter(
        field_name="expressions__name",
        lookup_expr="iexact",
        label=_("Expression (name)"),
        distinct=True,
    )
    expressions = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricFilterExpression.objects.all(),
        field_name="expressions",
        label=_("Expressions (ID)"),
    )

    class Meta:
        model = IPFabricFilter
        fields = (
            "id",
            "name",
            "description",
            "endpoint_id",
            "endpoint",
            "endpoint_path",
            "endpoints",
            "filter_type",
            "sync_id",
            "sync",
            "syncs",
            "expression_id",
            "expression",
            "expressions",
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


class IPFabricFilterExpressionFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search")

    ipfabric_filter_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricFilter.objects.all(),
        field_name="filters",
        label=_("Filter (ID)"),
    )
    ipfabric_filter = django_filters.CharFilter(
        field_name="filters__name",
        lookup_expr="iexact",
        label=_("Filters (name)"),
        distinct=True,
    )
    ipfabric_filters = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricFilter.objects.all(),
        field_name="filters",
        label=_("Filters (ID)"),
    )

    class Meta:
        model = IPFabricFilterExpression
        fields = (
            "id",
            "name",
            "description",
            "expression",
            "ipfabric_filter_id",
            "ipfabric_filter",
            "ipfabric_filters",
        )
        filter_overrides = {
            JSONField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {"lookup_expr": "icontains"},
            },
        }

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


class IPFabricEndpointFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search")

    endpoint = django_filters.CharFilter(
        field_name="endpoint",
        lookup_expr="iexact",
        label=_("Endpoint (Path)"),
    )
    ipfabric_filter_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricFilter.objects.all(),
        field_name="filters",
        label=_("IP Fabric Filter (ID)"),
    )
    ipfabric_filter = django_filters.CharFilter(
        field_name="filters__name",
        lookup_expr="iexact",
        label=_("IP Fabric Filter (name)"),
        distinct=True,
    )
    ipfabric_filters = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricFilter.objects.all(),
        field_name="filters",
        label=_("IP Fabric Filters"),
    )

    class Meta:
        model = IPFabricEndpoint
        fields = (
            "id",
            "name",
            "description",
            "endpoint",
            "ipfabric_filter_id",
            "ipfabric_filter",
            "ipfabric_filters",
        )

    def search(self, queryset, name, value):
        if not value.strip().rstrip("/"):
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(endpoint__icontains=value)
            | Q(description__icontains=value)
        )


class IPFabricTransformMapGroupFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search")

    class Meta:
        model = IPFabricTransformMapGroup
        fields = ("id", "name", "description")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


class IPFabricTransformMapFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search")
    group_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricTransformMapGroup.objects.all(),
        label=_("Transform Map Group (ID)"),
    )
    group = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricTransformMapGroup.objects.all(), label=_("Transform Map Group")
    )
    source_endpoint = django_filters.ModelChoiceFilter(
        queryset=IPFabricEndpoint.objects.all(), label=_("Source Endpoint")
    )
    source_endpoint_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricEndpoint.objects.all(),
        field_name="source_endpoint",
        label=_("Source Endpoint (ID)"),
    )
    source_endpoints = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricEndpoint.objects.all(),
        field_name="source_endpoint",
        label=_("Source Endpoints"),
    )

    class Meta:
        model = IPFabricTransformMap
        fields = (
            "id",
            "name",
            "group",
            "source_endpoint",
            "source_endpoint_id",
            "source_endpoints",
            "target_model",
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(group__name__icontains=value) | Q(name__icontains=value)
        )


class IPFabricTransformFieldFilterSet(BaseFilterSet):
    transform_map = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricTransformMap.objects.all(), label=_("Transform Map")
    )
    transform_map_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricTransformMap.objects.all(),
        field_name="transform_map",
        label=_("Transform Map (ID)"),
    )
    source_field = django_filters.CharFilter(
        field_name="source_field",
        lookup_expr="exact",
        label=_("Source Field"),
    )
    target_field = django_filters.CharFilter(
        field_name="target_field",
        lookup_expr="exact",
        label=_("Target Field"),
    )
    coalesce = django_filters.BooleanFilter(
        field_name="coalesce",
        label=_("Coalesce"),
    )

    class Meta:
        model = IPFabricTransformField
        fields = (
            "id",
            "transform_map",
            "transform_map_id",
            "source_field",
            "target_field",
            "coalesce",
            "template",
        )


class IPFabricRelationshipFieldFilterSet(BaseFilterSet):
    transform_map = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricTransformMap.objects.all(), label=_("Transform Map")
    )
    transform_map_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IPFabricTransformMap.objects.all(),
        field_name="transform_map",
        label=_("Transform Map (ID)"),
    )
    source_model = django_filters.ModelChoiceFilter(
        queryset=ContentType.objects.all(),
        field_name="source_model",
        label=_("Source Model"),
    )
    target_field = django_filters.CharFilter(
        field_name="target_field",
        lookup_expr="exact",
        label=_("Target Field"),
    )
    coalesce = django_filters.BooleanFilter(
        field_name="coalesce",
        label=_("Coalesce"),
    )

    class Meta:
        model = IPFabricRelationshipField
        fields = (
            "id",
            "transform_map",
            "transform_map_id",
            "source_model",
            "target_field",
            "coalesce",
            "template",
        )
