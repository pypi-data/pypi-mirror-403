from __future__ import annotations

from typing import Any, List, Optional
from typing_extensions import TypedDict


class InPersonLocation(TypedDict):
    id: str
    name: str
    address: dict[str, Any]
    geoCoordinates: Optional[dict[str, Any]]
    metadata: Optional[dict[str, str]]
    createdTimestamp: int
    lastUpdatedTimestamp: int


class InPersonLocationDeleted(TypedDict):
    id: str


class InPersonLocations(TypedDict):
    items: List[InPersonLocation]
    paginationToken: Optional[str]
