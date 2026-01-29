from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from typing import Any

import requests

from ..models import ProviderConfig
from .base import BaseProvider


class MoonshotProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        if not config.api_key:
            raise ValueError("Missing API key. Set AIDEF_API_KEY or use `set key ...`.")
        self._config = config

    def complete(self, messages: list[dict[str, Any]], *, stream: bool) -> str | Iterable[str]:
        url = self._config.api_base.rstrip("/") + "/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._config.api_key}",
        }
        payload = {
            "model": self._config.model,
            "messages": messages,
            "temperature": 0.7,
            "stream": bool(stream),
        }

        if not stream:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

        resp = requests.post(url, headers=headers, json=payload, timeout=120, stream=True)
        resp.raise_for_status()
        return self._iter_sse_chunks(resp)

    def _iter_sse_chunks(self, resp: requests.Response) -> Iterator[str]:
        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line.strip()
            if not line.startswith("data: "):
                continue

            data_str = line[6:]
            if data_str == "[DONE]":
                break

            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            content = (
                data.get("choices", [{}])[0].get("delta", {}) or {}
            ).get("content")
            if content:
                yield content
