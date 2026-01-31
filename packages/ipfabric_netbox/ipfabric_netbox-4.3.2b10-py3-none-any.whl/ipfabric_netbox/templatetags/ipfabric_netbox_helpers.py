import logging
from collections import OrderedDict
from typing import TYPE_CHECKING

from django import template
from django.apps import apps

if TYPE_CHECKING:
    from ipfabric_netbox.models import IPFabricSync

register = template.Library()

logger = logging.getLogger("ipfabric_netbox.helpers")


@register.filter()
def resolve_object(pk, model_path):
    """
    Usage: {{ pk|resolve_object:"app_label.ModelName" }}
    """
    try:
        app_label, model_name = model_path.split(".")
        model = apps.get_model(app_label, model_name)
        return model.objects.get(pk=pk)
    except Exception:
        return None


@register.filter()
def sort_parameters_hierarchical(
    parameters_dict: dict, sync_obj: "IPFabricSync | None" = None
) -> list:
    """
    Sort parameters hierarchically for IPFabricSync objects:
    1. 'groups' first
    2. Models in hierarchical order from IPFabricSync.get_model_hierarchy()

    For other objects, returns items unsorted.

    Usage: {{ object.parameters|sort_parameters_hierarchical:object }}
    """
    if not parameters_dict or not isinstance(parameters_dict, dict):
        return []

    try:
        group_ids = parameters_dict.get("groups", [])

        # Get the hierarchical model order from IPFabricSync
        model_hierarchy = sync_obj.__class__.get_model_hierarchy(group_ids)
        # Convert ContentType objects to app_label.model format
        hierarchy_order = [f"{ct.app_label}.{ct.model}" for ct in model_hierarchy]

        # Group models by app label while maintaining hierarchical order
        app_models = OrderedDict()
        for model_name in hierarchy_order:
            if "." in model_name:
                app_label = model_name.split(".")[0]
                if app_label not in app_models:
                    app_models[app_label] = []
                app_models[app_label].append(model_name)

        # Build sorted list: groups first, then all app models
        sorted_keys = []
        for app_label, models in app_models.items():
            sorted_keys.extend(models)

        result = []
        # Start with keys that weren't in the hierarchy
        for key, value in parameters_dict.items():
            if key not in sorted_keys:
                result.append((key, value))

        # Return items in the sorted order
        for key in sorted_keys:
            if key in parameters_dict:
                result.append((key, parameters_dict[key]))

        return result
    except Exception:
        # Fallback to simple alphabetical sort if something goes wrong
        logger.warning("Failed to sort parameters hierarchically", exc_info=True)
        return sorted(parameters_dict.items())
