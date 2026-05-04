import re
from collections import defaultdict

from django.core.management.base import BaseCommand
from dashboard.models import TideEvent

TIME_RE = re.compile(r'^\d{2}:\d{2}$')


class Command(BaseCommand):
    help = 'Validate tide events in the database for a year and port.'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, required=True)
        parser.add_argument('--port', type=str, default='Porto de Cabedelo')

    def handle(self, *args, **options):
        year = options['year']
        port = options['port']
        qs = TideEvent.objects.filter(port_name=port, date__year=year).order_by('date', 'time')
        n = qs.count()
        if n == 0:
            self.stdout.write(self.style.WARNING(f'No tide rows for {port} / {year}.'))
            return

        errors = []
        warnings = []
        dup_check = defaultdict(list)

        for ev in qs.iterator():
            t = ev.time.strftime('%H:%M')
            if not TIME_RE.match(t):
                errors.append(f'{ev.pk}: bad time {t!r}')
            if ev.height_m < -0.5 or ev.height_m > 5.0:
                warnings.append(f'{ev.date} {t}: extreme height {ev.height_m} m')
            dup_check[(ev.date, t)].append(ev.pk)

        for (d, t), ids in dup_check.items():
            if len(ids) > 1:
                errors.append(f'Duplicate {d} {t}: pks {ids}')

        prev = None
        for ev in qs.iterator():
            if prev and ev.datetime_local <= prev.datetime_local:
                errors.append(f'Non-monotonic datetime: {prev.pk} then {ev.pk}')
            prev = ev

        if errors:
            self.stdout.write(self.style.ERROR(f'{len(errors)} error(s):'))
            for e in errors[:40]:
                self.stdout.write(f'  - {e}')
        else:
            self.stdout.write(self.style.SUCCESS('No structural errors.'))

        if warnings:
            self.stdout.write(self.style.WARNING(f'{len(warnings)} height warning(s) (sample):'))
            for w in warnings[:15]:
                self.stdout.write(f'  - {w}')

        self.stdout.write(f'Total events: {n}')
