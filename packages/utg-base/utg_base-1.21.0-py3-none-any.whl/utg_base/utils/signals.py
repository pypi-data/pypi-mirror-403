import sys
import threading

from django.dispatch import Signal

app_ready = Signal()


def register_app_ready_signals():
    if any([arg in sys.argv for arg in ['runserver', 'gunicorn', 'uwsgi', 'core.wsgi', 'core.asgi']]):
        threading.Thread(target=app_ready.send, kwargs={'sender': True}, daemon=True).start()
