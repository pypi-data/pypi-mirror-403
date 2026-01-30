from __future__ import annotations

from typing import Optional, cast
from ryft_sdk.client import RyftClient
from ryft_sdk.models.in_person_orders.dto.in_person_orders import (
    InPersonOrder,
    InPersonOrders,
)


class InPersonOrdersClient:
    def __init__(self, client: RyftClient):
        self.client = client
        self.path = "in-person/orders"

    async def list(
        self,
        ascending: Optional[bool] = None,
        limit: Optional[int] = None,
        startsAfter: Optional[str] = None,
        account: Optional[str] = None,
    ) -> InPersonOrders:
        return cast(
            InPersonOrders,
            self.client.get(
                self.path,
                {
                    "ascending": ascending,
                    "limit": limit,
                    "startsAfter": startsAfter,
                },
                account=account,
            ),
        )

    async def get(self, id: str, account: Optional[str] = None) -> InPersonOrder:
        return cast(
            InPersonOrder, self.client.get(f"{self.path}/{id}", account=account)
        )
