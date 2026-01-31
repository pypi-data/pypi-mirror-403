from django.utils.translation import gettext as _
from netbox.plugins import PluginMenu
from netbox.plugins import PluginMenuButton
from netbox.plugins import PluginMenuItem

source = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabricsource_list",
    link_text=_("Sources"),
    buttons=[
        PluginMenuButton(
            link="plugins:ipfabric_netbox:ipfabricsource_add",
            title=_("Add"),
            icon_class="mdi mdi-plus-thick",
            permissions=["ipfabric_netbox.add_ipfabricsource"],
        )
    ],
    permissions=["ipfabric_netbox.view_ipfabricsource"],
)

snapshot = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabricsnapshot_list",
    link_text=_("Snapshots"),
    permissions=["ipfabric_netbox.view_ipfabricsnapshot"],
)

sync = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabricsync_list",
    link_text=_("Syncs"),
    buttons=[
        PluginMenuButton(
            link="plugins:ipfabric_netbox:ipfabricsync_add",
            title=_("Add"),
            icon_class="mdi mdi-plus-thick",
            permissions=["ipfabric_netbox.add_ipfabricsync"],
        )
    ],
    permissions=["ipfabric_netbox.view_ipfabricsync"],
)

ingestion = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabricingestion_list",
    link_text=_("Ingestions"),
    buttons=[],
    permissions=["ipfabric_netbox.view_ipfabricingestion"],
)

endpoint = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabricendpoint_list",
    link_text=_("Endpoints"),
    permissions=["ipfabric_netbox.view_ipfabricendpoint"],
    buttons=[],
)

filter = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabricfilter_list",
    link_text=_("Filters"),
    permissions=["ipfabric_netbox.view_ipfabricfilter"],
    buttons=[
        PluginMenuButton(
            link="plugins:ipfabric_netbox:ipfabricfilter_add",
            title=_("Add"),
            icon_class="mdi mdi-plus-thick",
            permissions=["ipfabric_netbox.add_ipfabricfilter"],
        )
    ],
)

filter_expression = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabricfilterexpression_list",
    link_text=_("Filter Expressions"),
    permissions=["ipfabric_netbox.view_ipfabricfilterexpression"],
    buttons=[
        PluginMenuButton(
            link="plugins:ipfabric_netbox:ipfabricfilterexpression_add",
            title=_("Add"),
            icon_class="mdi mdi-plus-thick",
            permissions=["ipfabric_netbox.add_ipfabricfilterexpression"],
        )
    ],
)

tmg = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabrictransformmapgroup_list",
    link_text=_("Transform Map Groups"),
    permissions=["ipfabric_netbox.view_ipfabrictransformmapgroup"],
    buttons=[
        PluginMenuButton(
            link="plugins:ipfabric_netbox:ipfabrictransformmapgroup_add",
            title=_("Add"),
            icon_class="mdi mdi-plus-thick",
            permissions=["ipfabric_netbox.add_ipfabrictransformmapgroup"],
        )
    ],
)

tm = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabrictransformmap_list",
    link_text=_("Transform Maps"),
    permissions=["ipfabric_netbox.view_ipfabrictransformmap"],
    buttons=[
        PluginMenuButton(
            link="plugins:ipfabric_netbox:ipfabrictransformmap_add",
            title=_("Add"),
            icon_class="mdi mdi-plus-thick",
            permissions=["ipfabric_netbox.add_ipfabrictransformmap"],
        )
    ],
)

tmf = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabrictransformfield_list",
    link_text=_("Transform Fields"),
    permissions=["ipfabric_netbox.view_ipfabrictransformfield"],
    buttons=[
        PluginMenuButton(
            link="plugins:ipfabric_netbox:ipfabrictransformfield_add",
            title=_("Add"),
            icon_class="mdi mdi-plus-thick",
            permissions=["ipfabric_netbox.add_ipfabrictransformfield"],
        )
    ],
)

tmr = PluginMenuItem(
    link="plugins:ipfabric_netbox:ipfabricrelationshipfield_list",
    link_text=_("Relationship Fields"),
    permissions=["ipfabric_netbox.view_ipfabricrelationshipfield"],
    buttons=[
        PluginMenuButton(
            link="plugins:ipfabric_netbox:ipfabricrelationshipfield_add",
            title=_("Add"),
            icon_class="mdi mdi-plus-thick",
            permissions=["ipfabric_netbox.add_ipfabricrelationshipfield"],
        )
    ],
)

menu = PluginMenu(
    label="IP Fabric",
    icon_class="mdi mdi-cloud-sync",
    groups=(
        (
            "Data Sync",
            (source, snapshot, sync, ingestion),
        ),
        (
            "Configuration",
            (endpoint, filter, filter_expression, tmg, tm, tmf, tmr),
        ),
    ),
)
