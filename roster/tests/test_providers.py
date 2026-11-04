import pytest

from roster.providers import (
    ManualProvider,
    available_providers,
    get_provider,
    sync_dj,
)

from .factories import make_dj


def test_registry_lists_manual():
    assert "manual" in available_providers()


def test_get_provider_unknown_raises():
    with pytest.raises(ValueError):
        get_provider("does-not-exist")


def test_get_provider_returns_instance():
    assert isinstance(get_provider("manual"), ManualProvider)


@pytest.mark.django_db
def test_manual_sync_is_noop():
    dj = make_dj()
    counts = sync_dj(dj, ManualProvider())
    assert counts == {"shows": 0, "releases": 0, "engagement": 0}
