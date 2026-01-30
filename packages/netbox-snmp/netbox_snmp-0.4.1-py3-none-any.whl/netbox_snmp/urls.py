from django.urls import include, path
from utilities.urls import get_model_urls
from . import views
from .models import TrapProfiles, UserProfiles, MIBTrees

app_name = "netbox_snmp"

urlpatterns = (
    # region TRAP PROFILES
    path(
        "traps/",
        include(get_model_urls("netbox_snmp", "trapprofiles", detail=False)),
    ),
    path(
        "traps/<int:pk>/",
        include(get_model_urls("netbox_snmp", "trapprofiles")),
    ),
    # endregion
    # region USER PROFILES
    path(
        "users/",
        include(get_model_urls("netbox_snmp", "userprofiles", detail=False)),
    ),
    path(
        "users/<int:pk>/",
        include(get_model_urls("netbox_snmp", "userprofiles")),
    ),
    # endregion
    # region MIB TREES
    path(
        "view/",
        include(get_model_urls("netbox_snmp", "mibtrees", detail=False)),
    ),
    path(
        "view/<int:pk>/",
        include(get_model_urls("netbox_snmp", "mibtrees")),
    ),
    # endregion
    # region NOTIFY
    path(
        "notify/",
        include(get_model_urls("netbox_snmp", "notifyprofiles", detail=False)),
    ),
    path(
        "notify/<int:pk>/",
        include(get_model_urls("netbox_snmp", "notifyprofiles")),
    ),
    # endregion
)
