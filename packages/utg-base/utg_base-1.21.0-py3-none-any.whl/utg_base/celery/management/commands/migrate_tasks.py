import importlib
import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Migrate tasks"

    def add_arguments(self, parser):
        parser.add_argument('--app', type=str, help="An optional argument", required=True)

    def handle(self, *args, **options):
        try:
            tasks = importlib.import_module(f"{options['app']}.tasks")
            tasks = tasks.tasks
            for task in tasks:
                celery_task, _ = PeriodicTask.objects.update_or_create(
                    name=task['name'],
                    defaults={
                        'crontab': self.get_crontab_schedule(task['crontab']),
                        'task': task['task'].name,
                        'args': json.dumps(task.get('args') or []),
                        'kwargs': json.dumps(task.get('kwargs') or {}),
                        'enabled': task.get('enabled', True),
                    }
                )
            self.stdout.write(
                self.style.SUCCESS('Successfully migrated tasks')
            )
        except ModuleNotFoundError:
            self.stdout.write(self.style.ERROR("Tasks module not found"))

    @staticmethod
    def get_crontab_schedule(crontab='* * * * *'):
        minute, hour, day_of_month, month_of_year, day_of_week = crontab.split(' ')
        cron, _ = CrontabSchedule.objects.get_or_create(
            minute=minute,
            hour=hour,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
            day_of_week=day_of_week,
        )
        return cron
