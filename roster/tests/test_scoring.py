import pytest

from roster.models import PopularityScore
from roster.scoring import recompute_all

from .factories import make_dj


@pytest.mark.django_db
def test_scores_are_bounded_and_ranked():
    top = make_dj(name="Top", spotify=5_000_000, ig=2_000_000, eng=9.0, confirmed_shows=5)
    low = make_dj(name="Low", spotify=100_000, ig=50_000, eng=3.0, confirmed_shows=0)
    assert recompute_all() == 2
    ts = PopularityScore.objects.get(dj=top).score
    ls = PopularityScore.objects.get(dj=low).score
    assert 0 <= ls <= 100
    assert 0 <= ts <= 100
    assert ts > ls


@pytest.mark.django_db
def test_recompute_is_idempotent():
    make_dj(name="A", spotify=1_000_000)
    recompute_all()
    recompute_all()
    assert PopularityScore.objects.count() == 1
