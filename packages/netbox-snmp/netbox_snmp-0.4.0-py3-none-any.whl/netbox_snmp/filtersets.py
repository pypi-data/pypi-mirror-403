from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from utilities.filtersets import register_filterset

# from utilities.filtersets import register_filterset
from .models import TrapProfiles, UserProfiles, MIBTrees, NotifyProfiles


# region TRAP PROFILES
@register_filterset
class TrapProfilesFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = TrapProfiles
        fields = [
            "id",
            "name",
            "version",
            "level",
            "target",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        qs_filter = Q(name__icontains=value) | Q(description__icontains=value) | Q(target__icontains=value)
        return queryset.filter(qs_filter)


# endregion


# region USER PROFILES
@register_filterset
class UserProfilesFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = UserProfiles
        fields = [
            "id",
            "name",
            "auth",
            "priv",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        qs_filter = Q(name__icontains=value) | Q(description__icontains=value) | Q(target__icontains=value)
        return queryset.filter(qs_filter)


# endregion


# region MIB TREES
@register_filterset
class MIBTreesFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = MIBTrees
        fields = [
            "id",
            "name",
            "view_type",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value) | Q(target__icontains=value) | Q(oid__contains=[value]))


# endregion


# region NOTIFY
@register_filterset
class NotifyProfilesFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = NotifyProfiles
        fields = ["name", "notification_type"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        qs_filter = Q(name__icontains=value) | Q(description__icontains=value) | Q(target__icontains=value)
        return queryset.filter(qs_filter)


# endregion
