from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm, NetBoxModelBulkEditForm
from utilities.forms.fields import CommentField, TagFilterField
from .models import TrapProfiles, UserProfiles, MIBTrees, NotifyProfiles
from django import forms


# region TRAP PROFILES
class TrapProfilesForm(NetBoxModelForm):
    comments = CommentField()

    class Meta:
        model = TrapProfiles
        fields = ["name", "level", "version", "target", "port", "description", "comments", "tags", "user_profile"]


class TrapProfilesFilterForm(NetBoxModelFilterSetForm):
    model = TrapProfiles
    q = forms.CharField(required=False, label="Search")

    tag = TagFilterField(model)


class TrapProfilesBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(max_length=200, required=False)

    model = TrapProfiles
    nullable_fields = [
        "description",
    ]


# endregion


# region USER PROFILES
class UserProfilesForm(NetBoxModelForm):
    comments = CommentField()

    class Meta:
        model = UserProfiles
        fields = [
            "name",
            "auth",
            "priv",
            "description",
            "comments",
            "tags",
        ]


class UserProfilesFilterForm(NetBoxModelFilterSetForm):
    model = UserProfiles
    q = forms.CharField(required=False, label="Search")

    tag = TagFilterField(model)


class UserProfilesBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(max_length=200, required=False)

    model = UserProfiles
    nullable_fields = [
        "description",
    ]


# endregion


# region MIB TREES
class MIBTreesForm(NetBoxModelForm):
    comments = CommentField()

    class Meta:
        model = MIBTrees
        fields = [
            "name",
            "oid",
            "view_type",
            "description",
            "comments",
            "tags",
        ]


class MIBTreesFilterForm(NetBoxModelFilterSetForm):
    model = MIBTrees
    q = forms.CharField(required=False, label="Search")

    tag = TagFilterField(model)


class MIBTreesBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(max_length=200, required=False)

    model = MIBTrees
    nullable_fields = [
        "description",
    ]


# endregion


# region NOTIFY
class NotifyProfilesForm(NetBoxModelForm):
    comments = CommentField()

    class Meta:
        model = NotifyProfiles
        fields = [
            "name",
            "notification_type",
            "description",
            "comments",
            "tags",
        ]


class NotifyProfilesFilterForm(NetBoxModelFilterSetForm):
    model = NotifyProfiles
    q = forms.CharField(required=False, label="Search")

    tag = TagFilterField(model)


class NotifyProfilesBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(max_length=200, required=False)

    model = NotifyProfiles
    nullable_fields = [
        "description",
    ]


# endregion
