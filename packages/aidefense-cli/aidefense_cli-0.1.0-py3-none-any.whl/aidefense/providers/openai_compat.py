from __future__ import annotations

from ..models import ProviderConfig
from .moonshot import MoonshotProvider


class OpenAICompatibleProvider(MoonshotProvider):
    """Same wire format as /chat/completions providers."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
