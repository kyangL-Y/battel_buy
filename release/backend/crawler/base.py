from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FetchResult:
    url: str
    status_code: int | None
    html: str | None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BaseFetcher:
    def fetch(self, url: str) -> FetchResult:
        raise NotImplementedError
