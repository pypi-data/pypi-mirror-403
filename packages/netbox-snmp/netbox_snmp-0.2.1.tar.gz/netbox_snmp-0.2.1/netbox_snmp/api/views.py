from netbox.api.viewsets import NetBoxModelViewSet
from ..models import TrapProfiles, UserProfiles, MIBTrees, NotifyProfiles
from .serializers import TrapProfilesSerializer, UserProfilesSerializer, MIBTreesSerializer, NotifyProfilesSerializer
from ..filtersets import TrapProfilesFilterSet, UserProfilesFilterSet, MIBTreesFilterSet, NotifyProfilesFilterSet
from rest_framework.routers import APIRootView


class RootView(APIRootView):
    def get_view_name(self):
        return "SNMP"


# region TRAP PROFILES
class TrapProfilesViewSet(NetBoxModelViewSet):
    queryset = TrapProfiles.objects.all()
    serializer_class = TrapProfilesSerializer
    filterset_class = TrapProfilesFilterSet


# endregion


# region TRAP PROFILES
class UserProfilesViewSet(NetBoxModelViewSet):
    queryset = UserProfiles.objects.all()
    serializer_class = UserProfilesSerializer
    filterset_class = UserProfilesFilterSet


# endregion


# region MIB TREES
class MIBTreesViewSet(NetBoxModelViewSet):
    queryset = MIBTrees.objects.all()
    serializer_class = MIBTreesSerializer
    filterset_class = MIBTreesFilterSet


# endregion


# region NOTIFY TREES
class NotifyProfilesViewSet(NetBoxModelViewSet):
    queryset = NotifyProfiles.objects.all()
    serializer_class = NotifyProfilesSerializer
    filterset_class = NotifyProfilesFilterSet


# endregion
