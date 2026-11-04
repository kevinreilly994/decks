"""Bulk-import DJs from a CSV file (CLI). See roster/importers.py for the format."""
from django.core.management.base import BaseCommand, CommandError

from roster.importers import import_djs_from_file


class Command(BaseCommand):
    help = "Bulk-import DJs from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        path = options["csv_path"]
        try:
            with open(path, "rb") as fh:
                result = import_djs_from_file(fh)
        except FileNotFoundError:
            raise CommandError(f"File not found: {path}")
        self.stdout.write(self.style.SUCCESS(
            f"Imported: {result['created']} created, {result['updated']} updated, "
            f"{len(result['errors'])} error(s)."
        ))
        for err in result["errors"]:
            self.stderr.write(err)
