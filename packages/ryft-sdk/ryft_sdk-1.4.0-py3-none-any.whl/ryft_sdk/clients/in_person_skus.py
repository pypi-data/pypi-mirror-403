from __future__ import annotations

from typing import Optional, cast
from ryft_sdk.client import RyftClient
from ryft_sdk.models.in_person_skus.dto.in_person_skus import (
    InPersonProductSku,
    InPersonProductSkus,
)


class InPersonSkusClient:
    def __init__(self, client: RyftClient):
        self.client = client
        self.path = "in-person/skus"

    async def list(
        self,
        country: str,
        limit: Optional[int] = None,
        startsAfter: Optional[str] = None,
        productId: Optional[str] = None,
    ) -> InPersonProductSkus:
        return cast(
            InPersonProductSkus,
            self.client.get(
                self.path,
                {
                    "country": country,
                    "limit": limit,
                    "startsAfter": startsAfter,
                    "productId": productId,
                },
            ),
        )

    async def get(self, id: str) -> InPersonProductSku:
        return cast(InPersonProductSku, self.client.get(f"{self.path}/{id}"))
