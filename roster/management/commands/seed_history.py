"""Backfill monthly engagement snapshots so trend charts render in the demo.

Uses each DJ latest snapshot as the current month and generates earlier months on
a gentle upward curve. Demo helper only; real history accrues via sync_roster.
"""
from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from roster.models import DJ, EngagementSnapshot


def _month_back(d, n):
    month = d.month - n
    year = d.year
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


class Command(BaseCommand):
    help = "Backfill monthly engagement snapshots for a demo trend history."

    def add_arguments(self, parser):
        parser.add_argument("--months", type=int, default=11)

    def handle(self, *args, **opts):
        months = opts["months"]
        created = 0
        for dj in DJ.objects.filter(is_active=True):
            latest = dj.latest_snapshot()
            if not latest:
                continue
            for i in range(1, months + 1):
                factor = max(0.1, 1 - i * 0.05)
                when = _month_back(latest.captured_on, i)
                _, was_created = EngagementSnapshot.objects.update_or_create(
                    dj=dj, captured_on=when,
                    defaults={
                        "spotify_monthly": int((latest.spotify_monthly or 0) * factor),
                        "instagram_followers": int((latest.instagram_followers or 0) * factor),
                        "tiktok_followers": int((latest.tiktok_followers or 0) * factor),
                        "soundcloud_followers": int((latest.soundcloud_followers or 0) * factor),
                        "engagement_rate": max(0.0, float(latest.engagement_rate or 0) - i * 0.2),
                        "source": "manual",
                    },
                )
                created += 1 if was_created else 0
        self.stdout.write(self.style.SUCCESS(f"Backfilled history; {created} snapshots created."))
