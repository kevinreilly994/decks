import pytest

from .factories import make_dj


@pytest.mark.django_db
def test_slug_autofilled_from_name():
    dj = make_dj(name="Nova Kane")
    assert dj.slug == "nova-kane"


@pytest.mark.django_db
def test_fee_display_range():
    dj = make_dj()
    dj.fee_min, dj.fee_max = 10_000, 20_000
    text = dj.fee_display
    assert "10k" in text and "20k" in text


@pytest.mark.django_db
def test_upcoming_and_past_shows_split_by_status():
    dj = make_dj(confirmed_shows=2)
    assert dj.upcoming_shows().count() == 2
    assert dj.past_shows().count() == 0


@pytest.mark.django_db
def test_snapshot_social_total():
    dj = make_dj(ig=100, tk=200, sc=300)
    assert dj.latest_snapshot().social_total == 600


@pytest.mark.django_db
def test_next_show_and_latest_snapshot_helpers():
    from roster.models import ShowStatus
    dj = make_dj(confirmed_shows=1)
    assert dj.latest_snapshot() is not None
    ns = dj.next_show()
    assert ns is not None and ns.status == ShowStatus.CONFIRMED
