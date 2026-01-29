from django.conf import settings
from netbox.plugins import PluginMenuButton, PluginMenuItem, PluginMenu

menu_items = (
    # region TRAP PROFILES
    PluginMenuItem(
        link="plugins:netbox_snmp:trapprofiles_list",
        link_text="Trap Profiles",
        buttons=(
            PluginMenuButton(
                link="plugins:netbox_snmp:trapprofiles_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
            ),
        ),
    ),
    # endregion
    # region USER PROFILES
    PluginMenuItem(
        link="plugins:netbox_snmp:userprofiles_list",
        link_text="User Profiles",
        buttons=(
            PluginMenuButton(
                link="plugins:netbox_snmp:userprofiles_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
            ),
        ),
    ),
    # endregion
    # region MIB TREES
    PluginMenuItem(
        link="plugins:netbox_snmp:mibtrees_list",
        link_text="MIB Trees",
        buttons=(
            PluginMenuButton(
                link="plugins:netbox_snmp:mibtrees_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
            ),
        ),
    ),
    # endregion
    # region NOTIFY
    PluginMenuItem(
        link="plugins:netbox_snmp:notifyprofiles_list",
        link_text="Notify Profiles",
        buttons=(
            PluginMenuButton(
                link="plugins:netbox_snmp:notifyprofiles_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
            ),
        ),
    ),
    # endregion
)
