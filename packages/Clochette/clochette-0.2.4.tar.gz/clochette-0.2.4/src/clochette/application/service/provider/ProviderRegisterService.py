from dataclasses import dataclass

from clochette.application.store.ProviderStore import ProviderStore
from clochette.provider.basic.BasicProviderFactory import BasicProviderFactory
from clochette.provider.google.GoogleProviderFactory import GoogleProviderFactory
from clochette.provider.microsoft.MicrosoftProviderFactory import (
    MicrosoftProviderFactory,
)
from clochette.provider.public.PublicProviderFactory import PublicProviderFactory


@dataclass
class ProviderRegisterService:
    """Service to register all available calendar providers in the ProviderStore."""

    _provider_store: ProviderStore
    _public_provider_factory: PublicProviderFactory
    _basic_provider_factory: BasicProviderFactory
    _google_provider_factory: GoogleProviderFactory
    _microsoft_provider_factory: MicrosoftProviderFactory

    def register_providers(self) -> None:
        """Register all calendar providers in the store."""
        providers = [
            self._public_provider_factory.create(),
            self._basic_provider_factory.create(),
            self._google_provider_factory.create(),
            self._microsoft_provider_factory.create(),
        ]

        self._provider_store.set_provider(providers)
