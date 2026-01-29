from netbox.plugins import PluginConfig


class SNMPConfig(PluginConfig):
    name = "netbox_snmp"
    verbose_name = "SNMP"
    description = "Track SNMP related objects"
    version = "0.4.0"
    author = "AGE Solutions"
    author_email = "michael.terrero@age.solutions"
    base_url = "snmp"
    default_settings = {
        "device_ext_page": "right",
        "top_level_menu": False,
    }


config = SNMPConfig
