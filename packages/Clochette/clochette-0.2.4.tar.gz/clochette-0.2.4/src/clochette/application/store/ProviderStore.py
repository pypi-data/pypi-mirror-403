from reactivex import Observable
from reactivex.subject import ReplaySubject

from clochette.application.service.provider.dto.ProviderDTO import ProviderDTO


class ProviderStore:
    """Store for available provider information."""

    _providers: ReplaySubject[list[ProviderDTO]]

    def __init__(self):
        self._providers = ReplaySubject(buffer_size=1)

    @property
    def providers(self) -> Observable[list[ProviderDTO]]:
        return self._providers

    def set_provider(self, providers: list[ProviderDTO]) -> None:
        self._providers.on_next(providers)
