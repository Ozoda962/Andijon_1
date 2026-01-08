import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# app.conf.beat_schedule = {
#     'run-every-midnight': {
#         'task': 'app.tasks.run_extract_data_from_csv_bp',
#         'schedule': 10,
#     },
# }

app.conf.beat_schedule = {
    'run-every-day-at-12': {
        'task': 'app.tasks.run_extract_data_from_csv_bp',
        'schedule': crontab(hour=15, minute=35),
    },
}