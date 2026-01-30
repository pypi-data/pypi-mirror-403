from __future__ import annotations

from typing import Any, List, Optional
from typing_extensions import TypedDict


class InPersonOrder(TypedDict):
    id: str
    status: str
    totalAmount: int
    taxAmount: int
    currency: str
    items: List[dict[str, Any]]
    shipping: Optional[dict[str, Any]]
    tracking: Optional[dict[str, Any]]
    metadata: Optional[dict[str, str]]
    createdTimestamp: int
    lastUpdatedTimestamp: int


class InPersonOrders(TypedDict):
    items: List[InPersonOrder]
    paginationToken: Optional[str]
