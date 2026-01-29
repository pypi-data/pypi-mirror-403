from pathlib import Path

from django.core.management import BaseCommand, call_command

from django_simple_dms.management.utils import PrintCommandMixin
from django_simple_dms.utils import import_csv
import sys


class Command(PrintCommandMixin, BaseCommand):
    help = 'Setup Demo data'

    def handle(self, *args, **options):
        call_command('migrate')

        path = Path(__file__).parents[4] / 'examples/example_rates.csv'
        if not path.exists():
            self.print('ERROR', f'File {path} does not exist', exit_code=1)
            sys.exit(1)
        results = import_csv(path)
        self.print(
            'WARNING' if results['skipped'] else 'SUCCESS',
            f'Loaded {results["loaded"]} records. Skipped {results["skipped"]} records.',
            exit_code=2 if results['skipped'] else 0,
        )
