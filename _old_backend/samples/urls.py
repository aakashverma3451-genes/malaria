from rest_framework.routers import SimpleRouter

from .views import (
    ProjectViewSet,
    RawFileViewSet,
    SampleViewSet,
    SequencingRunViewSet,
)

router = SimpleRouter()
router.register('projects', ProjectViewSet)
router.register('samples', SampleViewSet)
router.register('sequencing-runs', SequencingRunViewSet)
router.register('files', RawFileViewSet)

urlpatterns = router.urls
