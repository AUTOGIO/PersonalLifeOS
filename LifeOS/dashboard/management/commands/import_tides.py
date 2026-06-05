import json
import logging
import re
from datetime import date, datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from zoneinfo import ZoneInfo

from dashboard.models import TideEvent
from dashboard.services.tide_service import PORT_DEFAULT

logger = logging.getLogger(__name__)

TIME_RE = re.compile(r'^\d{2}:\d{2}$')


def _iter_records(raw):
    if isinstance(raw, dict) and 'events' in raw:
        raw = raw['events']
    if not isinstance(raw, list):
        raise CommandError('JSON root must be a list or an object with an "events" array.')
    for item in raw:
        if isinstance(item, dict) and 'model' in item and 'fields' in item:
            yield item['fields']
        elif isinstance(item, dict) and 'date' in item and 'time' in item:
            yield item
        else:
            logger.warning('Skipping unrecognized JSON row: %s', item)


def _parse_row(fields, port_override=None):
    port = port_override or fields.get('port_name') or PORT_DEFAULT
    d = fields['date']
    if hasattr(d, 'isoformat'):
        date_s = d.isoformat()
    else:
        date_s = str(d)
    time_s = fields['time']
    if hasattr(time_s, 'strftime'):
        time_s = time_s.strftime('%H:%M')
    else:
        time_s = str(time_s)[:5]
    if not TIME_RE.match(time_s):
        raise ValueError(f'Invalid time (expected HH:MM): {time_s!r}')
    height = float(fields['height_m'])
    tide_type = fields.get('tide_type') or 'UNKNOWN'
    if tide_type not in ('HIGH', 'LOW', 'UNKNOWN'):
        tide_type = 'UNKNOWN'
    source = fields.get('source') or 'Porto de Cabedelo 2026 tide table'
    tz_name = fields.get('timezone') or 'America/Fortaleza'
    raw_dt = fields.get('datetime_local')
    if raw_dt:
        if hasattr(raw_dt, 'isoformat'):
            dt_s = raw_dt.isoformat()
        else:
            dt_s = str(raw_dt).replace('Z', '')
        if 'T' not in dt_s:
            dt_s = f'{date_s}T{time_s}:00'
    else:
        dt_s = f'{date_s}T{time_s}:00'
    d_obj = date.fromisoformat(date_s)
    t_obj = datetime.strptime(time_s, '%H:%M').time()
    naive = datetime.combine(d_obj, t_obj)
    aware = timezone.make_aware(naive, ZoneInfo(tz_name))
    return {
        'port_name': port,
        'date': d_obj,
        'time': t_obj,
        'datetime_local': aware,
        'height_m': height,
        'tide_type': tide_type,
        'source': source,
        'timezone': tz_name,
    }


class Command(BaseCommand):
    help = 'Import tide events from JSON (fixture-style or flat rows).'

    def add_arguments(self, parser):
        parser.add_argument('json_path', type=str, help='Path to porto_cabedelo_2026.json')
        parser.add_argument(
            '--replace-year',
            type=int,
            default=None,
            help='Delete existing events for this port and year before import.',
        )
        parser.add_argument('--port', type=str, default=PORT_DEFAULT)

    def handle(self, *args, **options):
        path = Path(options['json_path']).expanduser()
        if not path.is_file():
            raise CommandError(f'File not found: {path}')
        port = options['port']

        raw = json.loads(path.read_text(encoding='utf-8'))
        rows = []
        warnings = []
        seen = set()
        for fields in _iter_records(raw):
            try:
                row = _parse_row(fields, port_override=port)
            except (ValueError, KeyError, TypeError) as e:
                warnings.append(str(e))
                continue
            key = (row['port_name'], row['date'], row['time'])
            if key in seen:
                warnings.append(f'Duplicate in file: {key}')
                continue
            seen.add(key)
            rows.append(row)

        if warnings:
            for w in warnings[:50]:
                logger.warning('%s', w)
            if len(warnings) > 50:
                logger.warning('... %s more warnings', len(warnings) - 50)

        with transaction.atomic():
            if options['replace_year']:
                y = options['replace_year']
                deleted, _ = TideEvent.objects.filter(
                    port_name=port, date__year=y
                ).delete()
                self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing rows for {port} / {y}'))
            to_create = [
                TideEvent(
                    port_name=r['port_name'],
                    date=r['date'],
                    time=r['time'],
                    datetime_local=r['datetime_local'],
                    height_m=r['height_m'],
                    tide_type=r['tide_type'],
                    source=r['source'],
                    timezone=r['timezone'],
                )
                for r in rows
            ]
            TideEvent.objects.bulk_create(to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f'Prepared {len(rows)} tide rows (bulk_create with ignore_conflicts).'))
