from netbox.tables import NetBoxTable, ChoiceFieldColumn
import django_tables2 as tables
from netbox.tables import NetBoxTable
from .models import TrapProfiles, UserProfiles, MIBTrees, NotifyProfiles


# region TRAP PROFILES
class TrapProfilesTable(NetBoxTable):
    name = tables.Column(linkify=True)
    user_profile = tables.Column(linkify=True)
    target = tables.Column()

    class Meta(NetBoxTable.Meta):
        model = TrapProfiles
        fields = ("pk", "level", "name", "port", "version", "user_profile", "target")
        default_columns = ("name", "level", "version", "port", "user_profile", "target")


# endregion


# region USER PROFILES
class UserProfilesTable(NetBoxTable):
    name = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = UserProfiles
        fields = ("pk", "level", "name", "auth", "priv")
        default_columns = ("name", "auth", "priv")


# endregion


# region MIB TREES
class MIBTreesTable(NetBoxTable):
    name = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = MIBTrees
        fields = ("pk", "name", "oid", "view_type")
        default_columns = ("name", "oid", "view_type")


# endregion


# region NOTIFY
class NotifyProfilesTable(NetBoxTable):
    name = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = NotifyProfiles
        fields = ("pk", "name", "notification_type")
        default_columns = ("name", "notification_type")


# endregion
