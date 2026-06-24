from rest_framework.routers import SimpleRouter

from .views import AnalysisJobViewSet, ResultViewSet

router = SimpleRouter()
router.register('jobs', AnalysisJobViewSet)
router.register('results', ResultViewSet)

urlpatterns = router.urls
