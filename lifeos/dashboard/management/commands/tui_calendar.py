"""
management/commands/tui_calendar.py — LifeOS
Launches the curses-based weekly TUI calendar.

Usage:
    python manage.py tui_calendar
"""

import sys
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Launch the LifeOS colorful TUI weekly calendar (curses-based, no extra deps)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--week',
            metavar='YYYY-MM-DD',
            help='Start on the week containing this date (default: current week)',
        )

    def handle(self, *args, **options):
        # Validate optional date arg before launching curses
        week_override = None
        if options.get('week'):
            from datetime import date, timedelta
            try:
                from datetime import datetime
                d = datetime.strptime(options['week'], '%Y-%m-%d').date()
                week_override = d - timedelta(days=d.weekday())
            except ValueError:
                self.stderr.write(
                    self.style.ERROR(f"Invalid date: {options['week']} — expected YYYY-MM-DD")
                )
                sys.exit(1)

        # Ensure curses is available (it ships with CPython on macOS/Linux)
        try:
            import curses  # noqa: F401
        except ImportError:
            self.stderr.write(self.style.ERROR(
                'curses is not available in this Python installation.\n'
                'On macOS/Linux it ships with the standard library; '
                'on Windows you may need windows-curses.'
            ))
            sys.exit(1)

        # Import the TUI module from the dashboard app
        try:
            from dashboard.tui_calendar import TUICalendar, _init_colors, launch
        except ImportError as exc:
            self.stderr.write(self.style.ERROR(f'Cannot import TUI module: {exc}'))
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS('Launching LifeOS TUI Calendar… (q to quit)'))

        if week_override:
            # Custom week: patch the TUI to start on the requested week
            import curses as _curses
            import traceback

            def _main(stdscr):
                tui = TUICalendar(stdscr, django_ok=True)
                tui.week_start = week_override
                tui._load_data()
                tui.run()

            try:
                _curses.wrapper(_main)
            except Exception:
                sys.stdout.write('\033[0m')
                traceback.print_exc()
                sys.exit(1)
        else:
            launch()
