from netbox.views import generic
from . import forms, tables, filtersets
from utilities.views import register_model_view
from .models import TrapProfiles, UserProfiles, MIBTrees, NotifyProfiles


# region TRAP PROFILE
@register_model_view(TrapProfiles)
class TrapProfilesView(generic.ObjectView):
    queryset = TrapProfiles.objects.all()
    template_name = "netbox_snmp/trapprofiles.html"


@register_model_view(TrapProfiles, "list", path="", detail=False)
class TrapProfilesListView(generic.ObjectListView):
    queryset = TrapProfiles.objects.all()
    filterset = filtersets.TrapProfilesFilterSet
    filterset_form = forms.TrapProfilesFilterForm
    table = tables.TrapProfilesTable


@register_model_view(TrapProfiles, "add", detail=False)
@register_model_view(TrapProfiles, "edit")
class TrapProfilesEditView(generic.ObjectEditView):
    queryset = TrapProfiles.objects.all()
    form = forms.TrapProfilesForm


@register_model_view(TrapProfiles, "delete")
class TrapProfilesDeleteView(generic.ObjectDeleteView):
    queryset = TrapProfiles.objects.all()
    default_return_url = "plugins:netbox_snmp:trapprofiles_list"


@register_model_view(TrapProfiles, "bulk_delete", detail=False)
class TrapProfilesBulkDeleteView(generic.BulkDeleteView):
    queryset = TrapProfiles.objects.all()
    table = tables.TrapProfilesTable
    default_return_url = "plugins:netbox_snmp:trapprofiles_list"


@register_model_view(TrapProfiles, "bulk_edit", path="edit", detail=False)
class TrapProfilesBulkEditView(generic.BulkEditView):
    queryset = TrapProfiles.objects.all()
    filterset = filtersets.TrapProfilesFilterSet
    table = tables.TrapProfilesTable
    form = forms.TrapProfilesBulkEditForm


# endregion


# region USER PROFILE
@register_model_view(UserProfiles)
class UserProfilesView(generic.ObjectView):
    queryset = UserProfiles.objects.all()
    template_name = "netbox_snmp/userprofiles.html"


@register_model_view(UserProfiles, "list", path="", detail=False)
class UserProfilesListView(generic.ObjectListView):
    queryset = UserProfiles.objects.all()
    filterset = filtersets.UserProfilesFilterSet
    filterset_form = forms.UserProfilesFilterForm
    table = tables.UserProfilesTable


@register_model_view(UserProfiles, "add", detail=False)
@register_model_view(UserProfiles, "edit")
class UserProfilesEditView(generic.ObjectEditView):
    queryset = UserProfiles.objects.all()
    form = forms.UserProfilesForm


@register_model_view(UserProfiles, "delete")
class UserProfilesDeleteView(generic.ObjectDeleteView):
    queryset = UserProfiles.objects.all()
    default_return_url = "plugins:netbox_snmp:userprofiles_list"


@register_model_view(UserProfiles, "bulk_delete", detail=False)
class UserProfilesBulkDeleteView(generic.BulkDeleteView):
    queryset = UserProfiles.objects.all()
    table = tables.UserProfilesTable
    default_return_url = "plugins:netbox_snmp:userprofiles_list"


@register_model_view(UserProfiles, "bulk_edit", path="edit", detail=False)
class UserProfilesBulkEditView(generic.BulkEditView):
    queryset = UserProfiles.objects.all()
    filterset = filtersets.UserProfilesFilterSet
    table = tables.UserProfilesTable
    form = forms.UserProfilesBulkEditForm


# endregion


# region MIB TREES
@register_model_view(MIBTrees)
class MIBTreesView(generic.ObjectView):
    queryset = MIBTrees.objects.all()
    template_name = "netbox_snmp/mibtrees.html"


@register_model_view(MIBTrees, "list", path="", detail=False)
class MIBTreesListView(generic.ObjectListView):
    queryset = MIBTrees.objects.all()
    filterset = filtersets.MIBTreesFilterSet
    filterset_form = forms.MIBTreesFilterForm
    table = tables.MIBTreesTable


@register_model_view(MIBTrees, "add", detail=False)
@register_model_view(MIBTrees, "edit")
class MIBTreesEditView(generic.ObjectEditView):
    queryset = MIBTrees.objects.all()
    form = forms.MIBTreesForm


@register_model_view(MIBTrees, "delete")
class MIBTreesDeleteView(generic.ObjectDeleteView):
    queryset = MIBTrees.objects.all()
    default_return_url = "plugins:netbox_snmp:mibtrees_list"


@register_model_view(MIBTrees, "bulk_delete", detail=False)
class MIBTreesBulkDeleteView(generic.BulkDeleteView):
    queryset = MIBTrees.objects.all()
    table = tables.MIBTreesTable
    default_return_url = "plugins:netbox_snmp:mibtrees_list"


@register_model_view(MIBTrees, "bulk_edit", path="edit", detail=False)
class MIBTreesBulkEditView(generic.BulkEditView):
    queryset = MIBTrees.objects.all()
    filterset = filtersets.MIBTreesFilterSet
    table = tables.MIBTreesTable
    form = forms.MIBTreesBulkEditForm


# endregion


# region NOTIFY
@register_model_view(NotifyProfiles)
class NotifyProfilesView(generic.ObjectView):
    queryset = NotifyProfiles.objects.all()
    template_name = "netbox_snmp/notifyprofiles.html"


@register_model_view(NotifyProfiles, "list", path="", detail=False)
class NotifyProfilesListView(generic.ObjectListView):
    queryset = NotifyProfiles.objects.all()
    filterset = filtersets.NotifyProfilesFilterSet
    filterset_form = forms.NotifyProfilesFilterForm
    table = tables.NotifyProfilesTable


@register_model_view(NotifyProfiles, "add", detail=False)
@register_model_view(NotifyProfiles, "edit")
class NotifyProfilesEditView(generic.ObjectEditView):
    queryset = NotifyProfiles.objects.all()
    form = forms.NotifyProfilesForm


@register_model_view(NotifyProfiles, "delete")
class NotifyProfilesDeleteView(generic.ObjectDeleteView):
    queryset = NotifyProfiles.objects.all()
    default_return_url = "plugins:netbox_snmp:notifyprofiles_list"


@register_model_view(NotifyProfiles, "bulk_delete", detail=False)
class NotifyProfilesBulkDeleteView(generic.BulkDeleteView):
    queryset = NotifyProfiles.objects.all()
    table = tables.NotifyProfilesTable
    default_return_url = "plugins:netbox_snmp:notifyprofiles_list"


@register_model_view(NotifyProfiles, "bulk_edit", path="edit", detail=False)
class NotifyProfilesBulkEditView(generic.BulkEditView):
    queryset = NotifyProfiles.objects.all()
    filterset = filtersets.NotifyProfilesFilterSet
    table = tables.NotifyProfilesTable
    form = forms.NotifyProfilesBulkEditForm


# endregion
