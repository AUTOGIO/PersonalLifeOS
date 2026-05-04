"""
management/commands/seed_weekly_schedule.py
───────────────────────────────────────────
Seeds the ScheduleBlock table from the canonical weekly schedule JSON.
Runs the ScheduleEngine validator on every block before saving.

Usage:
    python manage.py seed_weekly_schedule
    python manage.py seed_weekly_schedule --clear
    python manage.py seed_weekly_schedule --dry-run
"""

from datetime import time
from django.core.management.base import BaseCommand
from dashboard.models import ScheduleBlock
from dashboard.schedule_engine import ScheduleEngine


# ── Canonical weekly schedule (source of truth) ─────────────────────────────
# Derived from Life OS Planner v1.0 artifact
WEEKLY_SCHEDULE = [
    # ── MONDAY — AI Core (Deep Work Day 1) ──────────────────────────────
    {
        "day_of_week": "MON", "activity": "Dog Training",
        "start_time": time(8,  0), "end_time": time(9,  15), "duration_min": 75,
        "category": "Physical", "is_anchor": False, "display_order": 1,
    },
    {
        "day_of_week": "MON", "activity": "AI Dev — Core OS",
        "start_time": time(10, 30), "end_time": time(13, 0), "duration_min": 150,
        "category": "Core", "is_anchor": False, "display_order": 2,
        "notes": "Deep Work block — no interruptions",
    },
    {
        "day_of_week": "MON", "activity": "AI Dev — Core OS (cont.)",
        "start_time": time(14, 0), "end_time": time(15, 0), "duration_min": 60,
        "category": "Core", "is_anchor": False, "display_order": 3,
    },

    # ── TUESDAY — macOS + Muay Thai ─────────────────────────────────────
    {
        "day_of_week": "TUE", "activity": "Dog Training",
        "start_time": time(8,  0), "end_time": time(9,  15), "duration_min": 75,
        "category": "Physical", "is_anchor": False, "display_order": 1,
    },
    {
        "day_of_week": "TUE", "activity": "AI Dev — macOS Native",
        "start_time": time(10, 30), "end_time": time(13, 0), "duration_min": 150,
        "category": "macOS", "is_anchor": False, "display_order": 2,
        "notes": "Deep Work block — no interruptions",
    },
    {
        "day_of_week": "TUE", "activity": "Muay Thai",
        "start_time": time(16, 0), "end_time": time(17, 30), "duration_min": 90,
        "category": "Physical", "is_anchor": True, "display_order": 3,
    },

    # ── WEDNESDAY — AI Core (Deep Work Day 2 / Peak) ─────────────────────
    {
        "day_of_week": "WED", "activity": "Dog Training",
        "start_time": time(8,  0), "end_time": time(9,  15), "duration_min": 75,
        "category": "Physical", "is_anchor": False, "display_order": 1,
    },
    {
        "day_of_week": "WED", "activity": "AI Dev — Core OS",
        "start_time": time(10, 30), "end_time": time(13, 0), "duration_min": 150,
        "category": "Core", "is_anchor": False, "display_order": 2,
        "notes": "Deep Work block — no interruptions",
    },
    {
        "day_of_week": "WED", "activity": "AI Dev — Core OS (cont.)",
        "start_time": time(14, 0), "end_time": time(15, 30), "duration_min": 90,
        "category": "Core", "is_anchor": False, "display_order": 3,
    },

    # ── THURSDAY — Business Data + Muay Thai ─────────────────────────────
    {
        "day_of_week": "THU", "activity": "Dog Training",
        "start_time": time(8,  0), "end_time": time(9,  0), "duration_min": 60,
        "category": "Physical", "is_anchor": False, "display_order": 1,
    },
    {
        "day_of_week": "THU", "activity": "AI Dev — Business Data",
        "start_time": time(10, 30), "end_time": time(12, 30), "duration_min": 120,
        "category": "Business", "is_anchor": False, "display_order": 2,
    },
    {
        "day_of_week": "THU", "activity": "Muay Thai",
        "start_time": time(16, 0), "end_time": time(17, 30), "duration_min": 90,
        "category": "Physical", "is_anchor": True, "display_order": 3,
    },

    # ── FRIDAY — Tools / Scripts (Recovery Day) ───────────────────────────
    {
        "day_of_week": "FRI", "activity": "Dog Training",
        "start_time": time(8,  0), "end_time": time(9,  0), "duration_min": 60,
        "category": "Physical", "is_anchor": False, "display_order": 1,
    },
    {
        "day_of_week": "FRI", "activity": "AI Dev — Tools/Scripts",
        "start_time": time(10, 30), "end_time": time(12, 0), "duration_min": 90,
        "category": "Tools", "is_anchor": False, "display_order": 2,
    },
    {
        "day_of_week": "FRI", "activity": "Admin / Week Review",
        "start_time": time(14, 0), "end_time": time(15, 0), "duration_min": 60,
        "category": "Meta", "is_anchor": False, "display_order": 3,
    },

    # ── SATURDAY — macOS Native + Muay Thai ──────────────────────────────
    {
        "day_of_week": "SAT", "activity": "Dog Training",
        "start_time": time(8,  0), "end_time": time(9,  0), "duration_min": 60,
        "category": "Physical", "is_anchor": False, "display_order": 1,
    },
    {
        "day_of_week": "SAT", "activity": "AI Dev — macOS Native",
        "start_time": time(10, 30), "end_time": time(12, 30), "duration_min": 120,
        "category": "macOS", "is_anchor": False, "display_order": 2,
    },
    {
        "day_of_week": "SAT", "activity": "Muay Thai",
        "start_time": time(16, 0), "end_time": time(17, 30), "duration_min": 90,
        "category": "Physical", "is_anchor": True, "display_order": 3,
    },

    # ── SUNDAY — Full Recovery ────────────────────────────────────────────
    {
        "day_of_week": "SUN", "activity": "Dog Training",
        "start_time": time(8,  0), "end_time": time(9,  0), "duration_min": 60,
        "category": "Physical", "is_anchor": False, "display_order": 1,
    },
]


class Command(BaseCommand):
    help = 'Seed ScheduleBlock table from the canonical weekly schedule'

    def add_arguments(self, parser):
        parser.add_argument('--clear',   action='store_true', help='Clear existing ScheduleBlocks first')
        parser.add_argument('--dry-run', action='store_true', help='Validate only, do not save')

    def handle(self, *args, **options):
        engine = ScheduleEngine()
        dry_run = options['dry_run']

        if options['clear'] and not dry_run:
            deleted, _ = ScheduleBlock.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'  Cleared {deleted} existing schedule blocks.'))

        self.stdout.write(self.style.HTTP_INFO('\n── Life OS Schedule Engine — Validation Pass ──'))

        passed = 0
        failed = 0
        saved  = 0

        for block in WEEKLY_SCHEDULE:
            result = engine.validate(block)
            label  = f"{block['day_of_week']} | {block['start_time'].strftime('%H:%M')} {block['activity']}"

            if result.is_valid:
                passed += 1
                if not dry_run:
                    _, created = ScheduleBlock.objects.get_or_create(
                        day_of_week=block['day_of_week'],
                        activity=block['activity'],
                        start_time=block['start_time'],
                        defaults={
                            'end_time':      block['end_time'],
                            'duration_min':  block['duration_min'],
                            'category':      block['category'],
                            'is_anchor':     block.get('is_anchor', False),
                            'notes':         block.get('notes', ''),
                            'display_order': block.get('display_order', 0),
                        }
                    )
                    if created:
                        saved += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✅ {label}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'  ⚡ SKIP (exists): {label}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'  ✅ [DRY] {label}'))

                for w in result.warnings:
                    self.stdout.write(self.style.WARNING(f'     ⚠ {w}'))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f'  ❌ FAIL: {label}'))
                for e in result.errors:
                    self.stdout.write(self.style.ERROR(f'     ✗ {e}'))

        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('── Summary ──────────────────────────────────────'))
        self.stdout.write(self.style.SUCCESS(f'  Validated : {passed + failed} blocks'))
        self.stdout.write(self.style.SUCCESS(f'  Passed    : {passed}'))
        if failed:
            self.stdout.write(self.style.ERROR(f'  Failed    : {failed}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  Failed    : {failed}'))
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'  Saved     : {saved} new blocks'))
        self.stdout.write('')
