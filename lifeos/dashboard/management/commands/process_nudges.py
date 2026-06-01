from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Process due Telegram activity reminders once and exit.'

    def handle(self, *args, **options):
        from reminders.tasks import job_activity_reminders

        job_activity_reminders()
        self.stdout.write(self.style.SUCCESS('Processed due activity reminders.'))
