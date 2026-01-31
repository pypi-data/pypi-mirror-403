import time

from django.apps import apps
from django.core.cache import cache
from django.dispatch import receiver
from utg_base.permissions.utils import sync_permissions
from utg_base.utils.signals import app_ready


@receiver(app_ready)
def sync_perms(sender, **kwargs):
    # wait all apps ready
    while not apps.ready:
        time.sleep(0.1)

    # only run 1 time (not all gunicorn workers)
    if not cache.add("sync_perms", True, timeout=10):
        return
    sync_permissions()
