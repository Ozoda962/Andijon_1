from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule

class Command(BaseCommand):
    help = "Setup periodic task for sensors"

    def handle(self, *args, **options):
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute='21',
            hour='20',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )

        task, created = PeriodicTask.objects.update_or_create(
            name='Collect sensor data at 15:30',
            defaults={
                'crontab': schedule,
                'task': 'sensors.tasks.collect_sensor_data_if_today',
                'enabled': True,
            }
        )

        self.stdout.write(self.style.SUCCESS("Periodic task setup successfully"))
