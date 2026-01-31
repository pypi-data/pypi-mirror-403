from django.utils.translation import gettext_lazy as _
from utilities.choices import ChoiceSet

transform_field_source_columns = {
    "/inventory/sites/overview": [
        "id",
        "siteName",
        "devicesCount",
        "usersCount",
        "stpDCount",
        "switchesCount",
        "vlanCount",
        "rDCount",
        "routersCount",
        "networksCount",
    ],
    "/inventory/devices": [
        "id",
        "sn",
        "hostname",
        "siteName",
        "rd",
        "stpDomain",
        "snHw",
        "loginIp",
        "objectId",
        "loginType",
        "uptime",
        "reload",
        "memoryUtilization",
        "memoryTotalBytes",
        "memoryUsedBytes",
        "vendor",
        "family",
        "platform",
        "model",
        "configReg",
        "version",
        "image",
        "processor",
        "mac",
        "devType",
        "hostnameOriginal",
        "hostnameProcessed",
        "domain",
        "fqdn",
    ],
    "/inventory/part-numbers": [
        "id",
        "deviceSn",
        "hostname",
        "siteName",
        "deviceId",
        "name",
        "dscr",
        "pid",
        "sn",
        "vid",
        "vendor",
        "platform",
        "model",
    ],
    "/inventory/interfaces": [
        "id",
        "dscr",
        "duplex",
        "errDisabled",
        "hasTransceiver",
        "hostname",
        "intName",
        "intNameAlias",
        "l1",
        "l2",
        "loginIp",
        "loginType",
        "mac",
        "media",
        "mtu",
        "nameOriginal",
        "primaryIp",
        "reason",
        "rel",
        "siteName",
        "sn",
        "speed",
        "speedValue",
        "transceiverPn",
        "transceiverSn",
        "transceiverType",
    ],
    "/technology/vlans/site-summary": [
        "id",
        "siteName",
        "vlanId",
        "vlanName",
        "dscr",
        "devCount",
    ],
    "/technology/routing/vrf/detail": [
        "id",
        "sn",
        "hostname",
        "siteName",
        "vrf",
        "rd",
        "intCount",
    ],
    "/technology/networks/managed-networks": [
        "id",
        "siteName",
        "net",
        "hosts",
        "gw",
        "gwV",
        "vrf",
        "vlanId",
    ],
    "/technology/platforms/stack/members": [
        "id",
        "sn",
        "master",
        "siteName",
        "uptime",
        "member",
        "connectionsCount",
        "pn",
        "memberSn",
        "role",
        "state",
        "mac",
        "ver",
        "image",
        "hwVer",
    ],
    "/technology/addressing/managed-ip/ipv4": [
        "hostname",
        "sn",
        "intName",
        "stateL1",
        "stateL2",
        "siteName",
        "dnsName",
        "dnsHostnameMatch",
        "vlanId",
        "dnsReverseMatch",
        "mac",
        "ip",
        "net",
        "type",
        "vrf",
    ],
}

required_transform_map_contenttypes = [
    ("dcim", "site"),
    ("dcim", "manufacturer"),
    ("dcim", "platform"),
    ("dcim", "devicerole"),
    ("dcim", "devicetype"),
    ("dcim", "device"),
    ("dcim", "virtualchassis"),
    ("dcim", "interface"),
    ("dcim", "macaddress"),
    ("ipam", "vlan"),
    ("ipam", "vrf"),
    ("ipam", "prefix"),
    ("ipam", "ipaddress"),
    ("dcim", "inventoryitem"),
]


class IPFabricEndpointChoices(ChoiceSet):
    SITES = "/inventory/sites/overview"
    DEVICES = "/inventory/devices"
    VIRTUALCHASSIS = "/technology/platforms/stack/members"
    INTERFACES = "/inventory/interfaces"
    PARTNUMBERS = "/inventory/part-numbers"
    VLANS = "/technology/vlans/site-summary"
    VRFS = "/technology/routing/vrf/detail"
    PREFIXES = "/technology/networks/managed-networks"
    IPADDRESSES = "/technology/addressing/managed-ip/ipv4"

    CHOICES = (
        (SITES, SITES, "cyan"),
        (DEVICES, DEVICES, "gray"),
        (VIRTUALCHASSIS, VIRTUALCHASSIS, "grey"),
        (INTERFACES, INTERFACES, "gray"),
        (PARTNUMBERS, PARTNUMBERS, "gray"),
        (VLANS, VLANS, "gray"),
        (VRFS, VRFS, "gray"),
        (PREFIXES, PREFIXES, "gray"),
        (IPADDRESSES, IPADDRESSES, "gray"),
    )


class IPFabricFilterTypeChoices(ChoiceSet):
    AND = "and"
    OR = "or"

    CHOICES = (
        (AND, _("AND"), "blue"),
        (OR, _("OR"), "orange"),
    )


class IPFabricSnapshotStatusModelChoices(ChoiceSet):
    key = "IPFabricSnapshot.status"

    STATUS_LOADED = "loaded"
    STATUS_UNLOADED = "unloaded"

    CHOICES = [
        (STATUS_LOADED, _("Loaded"), "green"),
        (STATUS_UNLOADED, _("Unloaded"), "red"),
    ]


class IPFabricSourceTypeChoices(ChoiceSet):
    LOCAL = "local"
    REMOTE = "remote"

    CHOICES = (
        (LOCAL, _("Local"), "cyan"),
        (REMOTE, _("Remote"), "gray"),
    )


class IPFabricSyncParameterChoices(ChoiceSet):
    SITE = "dcim.site"
    DEVICE = "dcim.device"
    INTERFACE = "dcim.interface"
    VLAN = "ipam.vlan"
    VRF = "ipam.vrf"
    PREFIX = "ipam.prefix"
    IPADDRESS = "ipam.ipaddress"
    INVENTORYITEM = "dcim.inventoryitem"
    VIRTUALCHASSIS = "dcim.virtualchassis"
    PARTNUMBER = "dcim.partnumber"

    CHOICES = ()


class IPFabricRawDataTypeChoices(ChoiceSet):
    DEVICE = "device"
    VLAN = "vlan"
    VRF = "vrf"
    VIRTUALCHASSIS = "virtualchassis"
    PREFIX = "prefix"
    INTERFACE = "interface"
    IPADDRESS = "ipaddress"
    INVENTORYITEM = "inventoryitem"
    SITE = "site"

    CHOICES = (
        (DEVICE, _("Local"), "cyan"),
        (VLAN, _("VLAN"), "gray"),
        (VIRTUALCHASSIS, _("Virtual Chassis"), "gray"),
        (PREFIX, _("Prefix"), "gray"),
        (INTERFACE, _("Interface"), "gray"),
        (INVENTORYITEM, _("Inventory Item"), "gray"),
        (IPADDRESS, _("IP Address"), "gray"),
        (SITE, _("Site"), "gray"),
    )


class IPFabricSourceStatusChoices(ChoiceSet):
    NEW = "new"
    QUEUED = "queued"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"

    CHOICES = (
        (NEW, _("New"), "blue"),
        (QUEUED, _("Queued"), "orange"),
        (SYNCING, _("Syncing"), "cyan"),
        (COMPLETED, _("Completed"), "green"),
        (FAILED, _("Failed"), "red"),
    )


class IPFabricSyncStatusChoices(ChoiceSet):
    NEW = "new"
    QUEUED = "queued"
    SYNCING = "syncing"
    READY_TO_MERGE = "ready_to_merge"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"

    CHOICES = (
        (NEW, _("New"), "blue"),
        (QUEUED, _("Queued"), "orange"),
        (SYNCING, _("Syncing"), "cyan"),
        (READY_TO_MERGE, _("Ready to merge"), "purple"),
        (MERGING, _("Merging"), "cyan"),
        (COMPLETED, _("Completed"), "green"),
        (FAILED, _("Failed"), "red"),
    )
