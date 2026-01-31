from django.urls import path

from utg_base.api.routers import OptionalSlashRouter
from utg_base.celery.views import TaskResultViewSet, PeriodicTaskViewSet, PeriodicTaskRunNowView

router = OptionalSlashRouter()
router.register('task-results', TaskResultViewSet, basename='task-results')
router.register('periodic-tasks', PeriodicTaskViewSet, basename='periodic-tasks')

urlpatterns = [
    path('periodic-tasks/<pk>/run-now/', PeriodicTaskRunNowView.as_view(), name='periodic-tasks-run-now'),
]

urlpatterns += router.urls
