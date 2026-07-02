from rest_framework.routers import SimpleRouter

from .views import ReportViewSet

router = SimpleRouter()
router.register('reports', ReportViewSet)

urlpatterns = router.urls
