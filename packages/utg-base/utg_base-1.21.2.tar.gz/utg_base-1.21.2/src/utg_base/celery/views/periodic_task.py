import json

from celery import current_app
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, filters
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utg_base.api.permissions import IsSuperUser
from utg_base.celery.serializers import PeriodicTaskSerializer
from utg_base.utils.translation import translate as _


@extend_schema(tags=['admin/periodic-tasks'])
class PeriodicTaskViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'patch']
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer
    permission_classes = [IsSuperUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    @extend_schema(request={'application/json': PeriodicTaskSerializer()})
    def partial_update(self, request, *args, **kwargs):
        crontab = request.data.pop('crontab')
        response = super().partial_update(request, *args, **kwargs)

        if crontab:
            instance = self.get_object()
            crontab, _ = CrontabSchedule.objects.get_or_create(**crontab)

            instance.crontab = crontab
            instance.save()

        return Response(self.serializer_class(instance).data)


@extend_schema(tags=['admin/periodic-tasks'])
class PeriodicTaskRunNowView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            periodic_task = PeriodicTask.objects.get(pk=pk)
        except PeriodicTask.DoesNotExist:
            raise NotFound(detail=_("Periodic task not found"))

        if not periodic_task.enabled:
            raise ValidationError(detail=_("Task is disabled"))

        args = json.loads(periodic_task.args) if periodic_task.args else []
        kwargs = json.loads(periodic_task.kwargs) if periodic_task.kwargs else {}

        task = current_app.send_task(
            periodic_task.task,
            args=args,
            kwargs=kwargs,
            countdown=0,
            headers = {'periodic_task_name': periodic_task.name}
        )

        return Response({
            "detail": _("Task successfully triggered"),
            "task_id": task.id,
            "task_name": periodic_task.name,
            "celery_task": periodic_task.task,
        })
