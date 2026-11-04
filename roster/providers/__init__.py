"""Provider registry. get_provider(name) -> DataProvider instance."""
from __future__ import annotations

from .base import DataProvider, EngagementDTO, ReleaseDTO, ShowDTO
from .bandsintown import BandsintownProvider
from .manual import ManualProvider
from .spotify import SpotifyProvider
from .service import sync_dj

_REGISTRY: dict[str, type[DataProvider]] = {
    ManualProvider.name: ManualProvider,
    SpotifyProvider.name: SpotifyProvider,
    BandsintownProvider.name: BandsintownProvider,
}


def register(cls: type[DataProvider]) -> type[DataProvider]:
    _REGISTRY[cls.name] = cls
    return cls


def get_provider(name: str) -> DataProvider:
    try:
        return _REGISTRY[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown data provider: {name}") from exc


def available_providers() -> list[str]:
    return sorted(_REGISTRY)


__all__ = [
    "DataProvider", "ShowDTO", "ReleaseDTO", "EngagementDTO", "ManualProvider",
    "sync_dj", "get_provider", "register", "available_providers",
]
