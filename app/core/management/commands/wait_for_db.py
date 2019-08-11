import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):

    def handle(self, *args, **options):
        """Django command to wait for execution until db is available"""
        self.stdout.write('Connecting to database...')
        db_conn = None
        while not db_conn:
            try:
                db_conn = connections['default']
            except OperationalError:
                self.stdout.write('Database unavailable, waiting for 1 sec...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database available!'))
