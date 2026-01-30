from __future__ import annotations

from typing_extensions import TypedDict


class TemporaryAccountLink(TypedDict):
    url: str
    createdTimestamp: int
    expiresTimestamp: int
