"""Buyer-facing views (Phase 2). Server-rendered Django templates, internal-only.

All views require login; unauthenticated users are sent to the admin login
(settings.LOGIN_URL = "admin:login").
"""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .charts import sparkline
from .models import DJ, Genre, PopularityScore

SORTS = {
    "score": "-popularity__score",
    "trending": "-popularity__delta_7d",
    "name": "name",
}


def _shortlist_ids(request) -> list[int]:
    return request.session.get("shortlist", [])


@login_required
def directory(request):
    qs = DJ.objects.filter(is_active=True).select_related(
        "primary_genre", "popularity", "management"
    ).prefetch_related("snapshots", "shows")

    q = request.GET.get("q", "").strip()
    genre = request.GET.get("genre", "")
    sort = request.GET.get("sort", "score")

    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(primary_genre__name__icontains=q)
            | Q(home_base__icontains=q)
        )
    if genre:
        qs = qs.filter(primary_genre__slug=genre)

    qs = qs.order_by(SORTS.get(sort, SORTS["score"]), "name")

    return render(request, "roster/directory.html", {
        "djs": qs,
        "genres": Genre.objects.all(),
        "q": q,
        "active_genre": genre,
        "sort": sort,
        "shortlist": _shortlist_ids(request),
        "nav": "directory",
    })


@login_required
def dj_detail(request, slug):
    dj = get_object_or_404(
        DJ.objects.select_related("primary_genre", "popularity", "management"),
        slug=slug,
        is_active=True,
    )
    pop = getattr(dj, "popularity", None)
    rank = None
    if pop:
        rank = PopularityScore.objects.filter(score__gt=pop.score).count() + 1

    snaps = list(dj.snapshots.order_by("captured_on"))
    spotify_spark = sparkline([s.spotify_monthly for s in snaps])
    eng_spark = sparkline(
        [float(s.engagement_rate) if s.engagement_rate is not None else None for s in snaps]
    )

    return render(request, "roster/dj_detail.html", {
        "dj": dj,
        "pop": pop,
        "snapshot": dj.latest_snapshot(),
        "upcoming": dj.upcoming_shows(),
        "past": dj.past_shows(),
        "releases": dj.releases.all(),
        "socials": dj.socials.all(),
        "rank": rank,
        "total": DJ.objects.filter(is_active=True).count(),
        "in_shortlist": dj.id in _shortlist_ids(request),
        "spotify_spark": spotify_spark,
        "eng_spark": eng_spark,
        "snap_count": len(snaps),
        "nav": "",
    })


@login_required
def leaderboard(request):
    scores = PopularityScore.objects.select_related(
        "dj", "dj__primary_genre"
    ).order_by("-score")
    top = scores[0].score if scores else 1
    return render(request, "roster/leaderboard.html", {
        "scores": scores,
        "top": top or 1,
        "nav": "leaderboard",
    })


@login_required
def shortlist(request):
    ids = _shortlist_ids(request)
    djs = DJ.objects.filter(id__in=ids).select_related(
        "primary_genre", "popularity", "management"
    )
    return render(request, "roster/shortlist.html", {
        "djs": djs,
        "nav": "shortlist",
    })


@login_required
def shortlist_toggle(request, pk):
    if request.method == "POST":
        ids = request.session.get("shortlist", [])
        if pk in ids:
            ids.remove(pk)
        else:
            ids.append(pk)
        request.session["shortlist"] = ids
        request.session.modified = True
    return redirect(request.POST.get("next") or "roster:directory")
