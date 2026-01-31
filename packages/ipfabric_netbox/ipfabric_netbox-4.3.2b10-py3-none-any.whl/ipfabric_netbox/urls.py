from django.urls import include
from django.urls import path
from utilities.urls import get_model_urls

from . import views  # noqa: F401

# We need the blank views import so the views are already registered


urlpatterns = (
    # Source
    path(
        "source/",
        include(get_model_urls("ipfabric_netbox", "ipfabricsource", detail=False)),
    ),
    path(
        "source/<int:pk>/", include(get_model_urls("ipfabric_netbox", "ipfabricsource"))
    ),
    # Snapshot
    path(
        "snapshot/",
        include(get_model_urls("ipfabric_netbox", "ipfabricsnapshot", detail=False)),
    ),
    path(
        "snapshot/<int:pk>/",
        include(get_model_urls("ipfabric_netbox", "ipfabricsnapshot")),
    ),
    # Snapshot Data
    path(
        "data/",
        include(get_model_urls("ipfabric_netbox", "ipfabricdata", detail=False)),
    ),
    path("data/<int:pk>/", include(get_model_urls("ipfabric_netbox", "ipfabricdata"))),
    # Sync
    path(
        "sync/",
        include(get_model_urls("ipfabric_netbox", "ipfabricsync", detail=False)),
    ),
    path("sync/<int:pk>/", include(get_model_urls("ipfabric_netbox", "ipfabricsync"))),
    # Ingestion
    path(
        "ingestion/",
        include(get_model_urls("ipfabric_netbox", "ipfabricingestion", detail=False)),
    ),
    path(
        "ingestion/<int:pk>/",
        include(get_model_urls("ipfabric_netbox", "ipfabricingestion")),
    ),
    # Endpoint
    path(
        "filter/",
        include(get_model_urls("ipfabric_netbox", "ipfabricfilter", detail=False)),
    ),
    path(
        "filter/<int:pk>/",
        include(get_model_urls("ipfabric_netbox", "ipfabricfilter")),
    ),
    # Endpoint
    path(
        "filter-expression/",
        include(
            get_model_urls("ipfabric_netbox", "ipfabricfilterexpression", detail=False)
        ),
    ),
    # Test endpoint for unsaved expressions (no pk required)
    path(
        "filter-expression/test/",
        views.IPFabricFilterExpressionTestView.as_view(),
        name="ipfabricfilterexpression_test_no_pk",
    ),
    path(
        "filter-expression/<int:pk>/",
        include(get_model_urls("ipfabric_netbox", "ipfabricfilterexpression")),
    ),
    # Endpoint
    path(
        "endpoint/",
        include(get_model_urls("ipfabric_netbox", "ipfabricendpoint", detail=False)),
    ),
    path(
        "endpoint/<int:pk>/",
        include(get_model_urls("ipfabric_netbox", "ipfabricendpoint")),
    ),
    # Transform Map Group
    path(
        "transform-map-group/",
        include(
            get_model_urls("ipfabric_netbox", "ipfabrictransformmapgroup", detail=False)
        ),
    ),
    path(
        "transform-map-group/<int:pk>/",
        include(get_model_urls("ipfabric_netbox", "ipfabrictransformmapgroup")),
    ),
    # Transform Map
    path(
        "transform-map/",
        include(
            get_model_urls("ipfabric_netbox", "ipfabrictransformmap", detail=False)
        ),
    ),
    path(
        "transform-map/<int:pk>/",
        include(get_model_urls("ipfabric_netbox", "ipfabrictransformmap")),
    ),
    # Transform field
    path(
        "transform-field/",
        include(
            get_model_urls("ipfabric_netbox", "ipfabrictransformfield", detail=False)
        ),
    ),
    path(
        "transform-field/<int:pk>/",
        include(get_model_urls("ipfabric_netbox", "ipfabrictransformfield")),
    ),
    # Relationship Field
    path(
        "relationship-field/",
        include(
            get_model_urls("ipfabric_netbox", "ipfabricrelationshipfield", detail=False)
        ),
    ),
    path(
        "relationship-field/<int:pk>/",
        include(get_model_urls("ipfabric_netbox", "ipfabricrelationshipfield")),
    ),
)
