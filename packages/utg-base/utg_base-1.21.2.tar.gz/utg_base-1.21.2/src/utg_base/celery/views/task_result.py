import django_filters
from django_celery_results.models import TaskResult
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, filters

from utg_base.celery.filters import TaskResultFilterSet
from utg_base.api.permissions import IsSuperUser
from utg_base.celery.serializers import TaskResultSerializer


@extend_schema(tags=['admin/task-results'])
class TaskResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    permission_classes = [IsSuperUser]
    filterset_class = TaskResultFilterSet
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend]
    search_fields = ['name']
