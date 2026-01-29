from rest_framework.serializers import HyperlinkedIdentityField
from netbox.api.serializers import NetBoxModelSerializer

from ..models import TrapProfiles, UserProfiles, MIBTrees, NotifyProfiles


# region TRAP PROFILES
class TrapProfilesSerializer(NetBoxModelSerializer):
    url = HyperlinkedIdentityField(view_name="plugins-api:netbox_snmp-api:trapprofiles-detail")

    class Meta:
        model = TrapProfiles
        fields = ["id", "url", "display", "name", "version", "level", "target", "port", "timeout", "retries", "description", "tags", "custom_fields", "comments", "user_profile"]
        brief_fields = ("id", "url", "display", "name", "version", "level", "user_profile", "target")


# endregion


# region USER PROFILES
class UserProfilesSerializer(NetBoxModelSerializer):
    url = HyperlinkedIdentityField(view_name="plugins-api:netbox_snmp-api:userprofiles-detail")

    class Meta:
        model = UserProfiles
        fields = ["id", "url", "display", "name", "priv", "auth", "description", "tags", "custom_fields", "comments"]
        brief_fields = ("id", "url", "display", "name", "priv", "auth")


# endregion


# region MIB TREES
class MIBTreesSerializer(NetBoxModelSerializer):
    url = HyperlinkedIdentityField(view_name="plugins-api:netbox_snmp-api:mibtrees-detail")

    class Meta:
        model = MIBTrees
        fields = ["id", "url", "display", "name", "oid", "view_type", "description", "tags", "custom_fields", "comments"]
        brief_fields = ("id", "url", "display", "name", "oid", "view_type")


# endregion


# region NOTIFY TREES
class NotifyProfilesSerializer(NetBoxModelSerializer):
    url = HyperlinkedIdentityField(view_name="plugins-api:netbox_snmp-api:notifyprofiles-detail")

    class Meta:
        model = NotifyProfiles
        fields = ["id", "url", "display", "name", "notification_type", "description", "tags", "custom_fields", "comments"]
        brief_fields = ("id", "url", "display", "name", "notification_type")


# endregion
