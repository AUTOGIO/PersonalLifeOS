from datetime import date
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Refresh the local Cabedelo tide table used by the wind/tide dashboard.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=date.today().year,
            help='Tide year to replace and validate.',
        )
        parser.add_argument(
            '--json-path',
            type=str,
            default='',
            help='Override the default data/tides/porto_cabedelo_<year>.json path.',
        )

    def handle(self, *args, **options):
        year = options['year']
        if options['json_path']:
            json_path = Path(options['json_path']).expanduser()
        else:
            json_path = Path(__file__).resolve().parents[3] / 'data' / 'tides' / f'porto_cabedelo_{year}.json'

        if not json_path.is_file():
            raise CommandError(f'Tide JSON not found: {json_path}')

        call_command('import_tides', str(json_path), replace_year=year)
        call_command('validate_tides', year=year)
        self.stdout.write(self.style.SUCCESS(f'Cabedelo tide table refreshed for {year}.'))
