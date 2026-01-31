from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django_celery_results.models import TaskResult
from rest_framework import serializers


from utg_base.celery.serializers import TaskResultSerializer


class CrontabScheduleSerializer(serializers.ModelSerializer):
    timezone = serializers.SerializerMethodField()

    class Meta:
        model = CrontabSchedule
        fields = '__all__'

    def get_timezone(self, obj):
        return str(obj.timezone) if obj.timezone else None


class PeriodicTaskSerializer(serializers.ModelSerializer):
    crontab = CrontabScheduleSerializer(read_only=True)
    task_result = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PeriodicTask
        fields = '__all__'
        read_only_fields = ['name', 'task', 'args', 'kwargs', 'queue', 'exchange', 'routing_key', 'headers', 'priority',
                            'expires', 'expire_seconds', 'one_off', 'start_time', 'interval', 'solar', 'clocked']

    def get_task_result(self, obj):
        latest_task_result = TaskResult.objects.filter(
            periodic_task_name=obj.name
        ).order_by('-date_created').first()

        if not latest_task_result:
            return None

        return TaskResultSerializer(latest_task_result).data
