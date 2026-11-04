"""Recompute popularity scores for the whole active roster."""
from django.core.management.base import BaseCommand

from roster.scoring import recompute_all


class Command(BaseCommand):
    help = "Recompute PopularityScore for every active DJ."

    def handle(self, *args, **options):
        count = recompute_all()
        self.stdout.write(self.style.SUCCESS(f"Recomputed scores for {count} DJ(s)."))
