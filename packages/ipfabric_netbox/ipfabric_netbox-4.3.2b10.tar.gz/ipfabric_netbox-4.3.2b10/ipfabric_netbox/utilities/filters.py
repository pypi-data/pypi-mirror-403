import importlib.resources
import json

from netbox.settings import django_apps

from ..choices import IPFabricSourceTypeChoices

# region Filter Expression


def get_filter_expression_test_candidates(expression_instance):
    """
    Get potential LOCAL sources and endpoints from filters associated with a filter expression.

    Args:
        expression_instance: An IPFabricFilterExpression instance

    Returns:
        tuple: (sources_set, endpoints_set) - Sets of IPFabricSource and IPFabricEndpoint objects
    """
    if not expression_instance or not expression_instance.pk:
        return set(), set()

    sources = set()
    endpoints = set()

    # Query all filters that use this expression
    for filter_obj in expression_instance.filters.all():
        # Get LOCAL sources from syncs
        for sync in filter_obj.syncs.all():
            if (
                sync.snapshot_data
                and sync.snapshot_data.source
                and sync.snapshot_data.source.type == IPFabricSourceTypeChoices.LOCAL
            ):
                sources.add(sync.snapshot_data.source)

        # Get endpoints
        for endpoint in filter_obj.endpoints.all():
            endpoints.add(endpoint)

    return sources, endpoints


# endregion Filter Expression


# region Filter Creation

# These functions are used in the migration file to prepare the filters
# Because of this we have to use historical models
# see https://docs.djangoproject.com/en/5.1/topics/migrations/#historical-models


def build_filters(data, apps: django_apps = None, db_alias: str = "default") -> None:
    apps = apps or django_apps
    IPFabricEndpoint = apps.get_model("ipfabric_netbox", "IPFabricEndpoint")
    IPFabricFilter = apps.get_model("ipfabric_netbox", "IPFabricFilter")
    IPFabricFilterExpression = apps.get_model(
        "ipfabric_netbox", "IPFabricFilterExpression"
    )
    for expressions_data in data["expressions"]:
        IPFabricFilterExpression.objects.using(db_alias).create(**expressions_data)
    for filter_data in data["filters"]:
        filter_data["filter_type"] = "and"
        endpoints = [
            IPFabricEndpoint.objects.filter(endpoint=endpoint).first()
            for endpoint in filter_data.pop("endpoints", [])
        ]
        expressions = [
            IPFabricFilterExpression.objects.filter(name=expr).first()
            for expr in filter_data.pop("expressions", [])
        ]
        _filter = IPFabricFilter.objects.using(db_alias).create(**filter_data)
        _filter.endpoints.set(endpoints)
        _filter.expressions.set(expressions)


def get_filter_data() -> dict:
    for data_file in importlib.resources.files("ipfabric_netbox.data").iterdir():
        if data_file.name != "filters.json":
            continue
        with open(data_file, "rb") as data_file:
            return json.load(data_file)
    raise FileNotFoundError("'filters.json' not found in installed package")


# endregion Filter Creation
