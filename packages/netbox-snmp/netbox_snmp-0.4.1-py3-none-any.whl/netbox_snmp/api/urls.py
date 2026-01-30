from netbox.api.routers import NetBoxRouter
from .views import TrapProfilesViewSet, RootView, UserProfilesViewSet, MIBTreesViewSet, NotifyProfilesViewSet

router = NetBoxRouter()
router.APIRootView = RootView
router.register("trapprofiles", TrapProfilesViewSet)
router.register("userprofiles", UserProfilesViewSet)
router.register("mibtrees", MIBTreesViewSet)
router.register("notifyprofiles", NotifyProfilesViewSet)
urlpatterns = router.urls
