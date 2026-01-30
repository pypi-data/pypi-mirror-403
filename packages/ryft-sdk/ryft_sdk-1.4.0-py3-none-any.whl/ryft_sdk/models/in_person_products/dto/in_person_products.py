from __future__ import annotations

from typing import Any, List, Optional
from typing_extensions import TypedDict


class InPersonProduct(TypedDict):
    id: str
    name: str
    status: str
    description: str
    details: dict[str, str]
    createdTimestamp: int
    lastUpdatedTimestamp: int


class InPersonProducts(TypedDict):
    items: List[InPersonProduct]
    paginationToken: Optional[str]
