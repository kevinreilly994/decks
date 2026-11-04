"""Sync the roster from live providers and snapshot engagement.

Runs each configured provider (settings.DECKS_SYNC_PROVIDERS) that has credentials,
maps results onto the models (stamped by provider so manual data is preserved),
then recomputes popularity scores. Built to run on a schedule.
"""
from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand

from roster.models import DJ
from roster.providers import get_provider
from roster.providers.service import sync_dj
from roster.scoring import recompute_all


class Command(BaseCommand):
    help = "Sync roster data from live providers and recompute scores."

    def add_arguments(self, parser):
        parser.add_argument("--provider", action="append", dest="providers")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        names = opts.get("providers") or settings.DECKS_SYNC_PROVIDERS
        providers = []
        for name in names:
            try:
                provider = get_provider(name)
            except ValueError:
                self.stderr.write(f"Unknown provider: {name}")
                continue
            is_configured = getattr(type(provider), "is_configured", lambda: True)
            if not is_configured():
                self.stdout.write(self.style.WARNING(f"Skipping {name}: not configured."))
                continue
            providers.append(provider)

        if not providers:
            self.stdout.write(self.style.WARNING("No configured providers; nothing synced."))
            return

        djs = DJ.objects.filter(is_active=True)
        totals = {"shows": 0, "releases": 0, "engagement": 0}
        for dj in djs:
            for provider in providers:
                if opts.get("dry_run"):
                    self.stdout.write(f"[dry-run] {dj.name} via {provider.name}")
                    continue
                try:
                    counts = sync_dj(dj, provider)
                except Exception as exc:  # per-DJ resilience for a scheduled job
                    self.stderr.write(f"{dj.name} via {provider.name} failed: {exc}")
                    continue
                for key in totals:
                    totals[key] += counts[key]

        if opts.get("dry_run"):
            return
        recompute_all()
        self.stdout.write(self.style.SUCCESS(
            f"Synced {djs.count()} DJ(s): {totals['shows']} shows, "
            f"{totals['releases']} releases, {totals['engagement']} snapshots. "
            "Scores recomputed."
        ))
