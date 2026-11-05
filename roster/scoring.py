"""Popularity scoring for the Decks roster.

Each component is min-max normalized across the active roster to 0-100, then
combined with the weights in settings.DECKS_SCORE_WEIGHTS. Idempotent: safe to
run repeatedly / on a schedule.
"""
from __future__ import annotations

from django.conf import settings

from .models import DJ, PopularityScore, ShowStatus

COMPONENTS = ("streaming", "social", "engagement", "demand")


def _norm(value: float, lo: float, hi: float) -> int:
    if hi <= lo:
        return 0
    return max(0, min(100, round((value - lo) / (hi - lo) * 100)))


def recompute_all() -> int:
    """Recompute PopularityScore for every active DJ. Bulk-loaded and atomic."""
    from django.db import transaction
    from django.db.models import Count

    from .models import EngagementSnapshot, Show

    djs = list(DJ.objects.filter(is_active=True))
    if not djs:
        return 0
    ids = [d.pk for d in djs]

    latest = {}
    for snap in EngagementSnapshot.objects.filter(dj_id__in=ids).order_by("dj_id", "-captured_on"):
        latest.setdefault(snap.dj_id, snap)
    demand = {
        r["dj_id"]: r["c"]
        for r in Show.objects.filter(dj_id__in=ids, status=ShowStatus.CONFIRMED)
        .values("dj_id").annotate(c=Count("id"))
    }
    prev = {p.dj_id: p.score for p in PopularityScore.objects.filter(dj_id__in=ids)}

    raw = {}
    for d in djs:
        snap = latest.get(d.pk)
        raw[d.pk] = {
            "streaming": float(snap.spotify_monthly or 0) if snap else 0.0,
            "social": float(snap.social_total) if snap else 0.0,
            "engagement": float(snap.engagement_rate or 0) if snap else 0.0,
            "demand": float(demand.get(d.pk, 0)),
        }
    bounds = {
        k: (min(raw[d.pk][k] for d in djs), max(raw[d.pk][k] for d in djs))
        for k in COMPONENTS
    }
    weights = settings.DECKS_SCORE_WEIGHTS

    updated = 0
    with transaction.atomic():
        for d in djs:
            comp = {k: _norm(raw[d.pk][k], *bounds[k]) for k in COMPONENTS}
            score = round(sum(weights[k] * comp[k] for k in COMPONENTS))
            prev_score = prev.get(d.pk, score)
            PopularityScore.objects.update_or_create(
                dj=d,
                defaults={
                    "score": score,
                    "streaming_component": comp["streaming"],
                    "social_component": comp["social"],
                    "engagement_component": comp["engagement"],
                    "demand_component": comp["demand"],
                    "delta_7d": score - prev_score,
                },
            )
            updated += 1
    return updated
