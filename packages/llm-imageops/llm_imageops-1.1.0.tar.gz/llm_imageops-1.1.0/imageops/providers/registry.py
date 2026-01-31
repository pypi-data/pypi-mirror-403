"""Provider registry for managing providers."""

from typing import Dict
from .base import BaseProvider
from .anthropic import AnthropicProvider
from ..exceptions import ProviderNotFoundError


_PROVIDERS: Dict[str, BaseProvider] = {
    "anthropic": AnthropicProvider()
}


def get_provider(name: str) -> BaseProvider:
    """Get provider by name."""
    provider = _PROVIDERS.get(name.lower())
    if provider is None:
        raise ProviderNotFoundError(
            f"Provider '{name}' not found. Available providers: {list(_PROVIDERS.keys())}"
        )
    return provider


def register_provider(name: str, provider: BaseProvider):
    """Register a custom provider."""
    _PROVIDERS[name.lower()] = provider

