from __future__ import annotations

from typing import Any, List, Optional
from typing_extensions import TypedDict


class Terminal(TypedDict):
    id: str
    name: str
    location: dict[str, str]
    device: dict[str, Any]
    action: Optional[dict[str, Any]]
    metadata: Optional[dict[str, str]]
    createdTimestamp: int
    lastUpdatedTimestamp: int


class TerminalDeleted(TypedDict):
    id: str


class Terminals(TypedDict):
    items: List[Terminal]
    paginationToken: Optional[str]
