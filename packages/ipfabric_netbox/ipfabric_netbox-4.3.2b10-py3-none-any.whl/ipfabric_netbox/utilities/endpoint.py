import importlib.resources
import json

from netbox.settings import django_apps


# region Endpoint Creation

# These functions are used in the migration file to prepare the endpoints
# Because of this we have to use historical models
# see https://docs.djangoproject.com/en/5.1/topics/migrations/#historical-models


def build_endpoints(data, apps: django_apps = None, db_alias: str = "default") -> None:
    apps = apps or django_apps
    IPFabricEndpoint = apps.get_model("ipfabric_netbox", "IPFabricEndpoint")
    for endpoint_data in data:
        IPFabricEndpoint.objects.using(db_alias).create(**endpoint_data)


def get_endpoint_data() -> dict:
    for data_file in importlib.resources.files("ipfabric_netbox.data").iterdir():
        if data_file.name != "endpoint.json":
            continue
        with open(data_file, "rb") as data_file:
            return json.load(data_file)
    raise FileNotFoundError("'endpoint.json' not found in installed package")


# endregion Endpoint Creation
