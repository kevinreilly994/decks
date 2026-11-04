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


def _raw_components(dj: DJ) -> dict[str, float]:
    snap = dj.latest_snapshot()
    return {
        "streaming": float(snap.spotify_monthly or 0) if snap else 0.0,
        "social": float(snap.social_total) if snap else 0.0,
        "engagement": float(snap.engagement_rate or 0) if snap else 0.0,
        "demand": float(dj.shows.filter(status=ShowStatus.CONFIRMED).count()),
    }


def recompute_all() -> int:
    """Recompute PopularityScore for every active DJ. Returns the count updated."""
    djs = list(DJ.objects.filter(is_active=True))
    if not djs:
        return 0

    raw = {dj.pk: _raw_components(dj) for dj in djs}
    bounds = {
        key: (min(raw[dj.pk][key] for dj in djs), max(raw[dj.pk][key] for dj in djs))
        for key in COMPONENTS
    }
    weights = settings.DECKS_SCORE_WEIGHTS

    updated = 0
    for dj in djs:
        comp = {k: _norm(raw[dj.pk][k], *bounds[k]) for k in COMPONENTS}
        score = round(sum(weights[k] * comp[k] for k in COMPONENTS))
        prev = PopularityScore.objects.filter(dj=dj).first()
        prev_score = prev.score if prev else score
        PopularityScore.objects.update_or_create(
            dj=dj,
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
