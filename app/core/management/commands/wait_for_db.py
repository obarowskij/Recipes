"""
Django command to wait for the database to be available.
"""

from django.core.management.base import BaseCommand
from psycopg2 import OperationalError as Psycopg2OpError
from django.db.utils import OperationalError
from time import sleep


class Command(BaseCommand):
    """Django command to wait for database."""

    def handle(self, *args, **options):
        """Handle the command."""
        self.stdout.write("Waiting for database...")
        db_ready = False
        while db_ready is False:
            try:
                self.check(databases=["default"])
                db_ready = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write("Database unavailable, waiting 1 second...")
                sleep(1)
        self.stdout.write(self.style.SUCCESS("Database available!"))
