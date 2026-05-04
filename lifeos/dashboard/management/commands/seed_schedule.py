from datetime import date, timedelta, time
from django.core.management.base import BaseCommand
from dashboard.models import Activity, AIProject


WEEKDAYS = {0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU', 4: 'FRI', 5: 'SAT', 6: 'SUN'}

AI_PROJECTS = [
    {'name': 'PersonalLifeOS',      'category': 'CORE_OS',       'priority': 'HIGH'},
    {'name': 'life-command-center', 'category': 'CORE_OS',       'priority': 'HIGH'},
    {'name': 'fulofilo-analytics',  'category': 'BUSINESS_DATA', 'priority': 'HIGH'},
    {'name': 'GMC',                 'category': 'BUSINESS_DATA', 'priority': 'MEDIUM'},
    {'name': 'CORTEX',              'category': 'MACOS_NATIVE',  'priority': 'MEDIUM'},
    {'name': 'SwiftOrganizerX',     'category': 'MACOS_NATIVE',  'priority': 'MEDIUM'},
    {'name': 'claude-skills-os',    'category': 'TOOLS_SCRIPTS', 'priority': 'LOW'},
]


class Command(BaseCommand):
    help = 'Seed the next 30 days with a fixed schedule and AI projects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing PLANNED activities before seeding'
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = Activity.objects.filter(status='PLANNED').delete()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} planned activities.'))

        # ── Seed AI Projects ──────────────────────────────────────────────────
        created_projects = 0
        for proj in AI_PROJECTS:
            _, created = AIProject.objects.get_or_create(
                name=proj['name'],
                defaults={
                    'category': proj['category'],
                    'priority': proj['priority'],
                    'status': 'ACTIVE',
                }
            )
            if created:
                created_projects += 1
        self.stdout.write(self.style.SUCCESS(f'✅ {created_projects} AI Projects seeded.'))

        # ── Seed 30-day Schedule ──────────────────────────────────────────────
        today = date.today()
        created_activities = 0

        for i in range(30):
            day = today + timedelta(days=i)
            wd = day.weekday()  # 0=Mon … 6=Sun
            day_name = WEEKDAYS[wd]
            activities_for_day = self._build_day_schedule(day, wd, day_name)

            for act_data in activities_for_day:
                _, created = Activity.objects.get_or_create(
                    name=act_data['name'],
                    scheduled_date=act_data['scheduled_date'],
                    start_time=act_data['start_time'],
                    defaults={
                        'category': act_data['category'],
                        'end_time': act_data['end_time'],
                        'status': 'PLANNED',
                        'notes': act_data.get('notes', ''),
                    }
                )
                if created:
                    created_activities += 1

        self.stdout.write(
            self.style.SUCCESS(f'✅ {created_activities} activities seeded across 30 days.')
        )

    def _build_day_schedule(self, day, wd, day_name):
        """Return list of activity dicts for a given day."""
        activities = []

        # ── Sleep Block (informational) ───────────────────────────────────────
        activities.append({
            'name': 'Sleep',
            'category': 'SLEEP',
            'scheduled_date': day,
            'start_time': time(23, 0),
            'end_time': time(23, 59),
            'notes': 'Sleep block 23:00–07:00 (next day)',
        })

        # ── Gym: Mon/Wed/Fri/Sat/Sun (not Tue, not Thu) ───────────────────────
        if day_name not in ('TUE', 'THU'):
            activities.append({
                'name': 'Gym',
                'category': 'GYM',
                'scheduled_date': day,
                'start_time': time(8, 15),
                'end_time': time(9, 30),
            })

        # ── Dog Training: every day 08:00–10:00 ──────────────────────────────
        activities.append({
            'name': 'Dog Training',
            'category': 'DOG_TRAINING',
            'scheduled_date': day,
            'start_time': time(8, 0),
            'end_time': time(10, 0),
        })

        # ── Muay Thai: Mon + Wed, 16:00–18:00 ────────────────────────────────
        if day_name in ('MON', 'WED'):
            activities.append({
                'name': 'Muay Thai',
                'category': 'MUAY_THAI',
                'scheduled_date': day,
                'start_time': time(16, 0),
                'end_time': time(18, 0),
            })

        # ── AI Dev blocks: weekdays only ──────────────────────────────────────
        if day_name in ('MON', 'TUE', 'WED', 'THU', 'FRI'):
            # Morning block: alternate Core / Business
            morning_cat = 'AI_DEV_CORE' if wd % 2 == 0 else 'AI_DEV_BUSINESS'
            activities.append({
                'name': f'AI Dev — {"Core" if morning_cat == "AI_DEV_CORE" else "Business"}',
                'category': morning_cat,
                'scheduled_date': day,
                'start_time': time(10, 0),
                'end_time': time(12, 30),
                'notes': 'Flexible AI development block',
            })
            # Afternoon block: alternate macOS / Tools
            afternoon_cat = 'AI_DEV_MACOS' if wd % 2 == 0 else 'AI_DEV_TOOLS'
            activities.append({
                'name': f'AI Dev — {"macOS" if afternoon_cat == "AI_DEV_MACOS" else "Tools"}',
                'category': afternoon_cat,
                'scheduled_date': day,
                'start_time': time(14, 0),
                'end_time': time(16, 0),
                'notes': 'Flexible AI development block',
            })

        return activities
