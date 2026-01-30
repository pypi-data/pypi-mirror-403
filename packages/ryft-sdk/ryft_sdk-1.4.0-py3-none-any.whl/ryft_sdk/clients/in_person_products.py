from __future__ import annotations

from typing import Optional, cast
from ryft_sdk.client import RyftClient
from ryft_sdk.models.in_person_products.dto.in_person_products import (
    InPersonProduct,
    InPersonProducts,
)


class InPersonProductsClient:
    def __init__(self, client: RyftClient):
        self.client = client
        self.path = "in-person/products"

    async def list(
        self,
        ascending: Optional[bool] = None,
        limit: Optional[int] = None,
        startsAfter: Optional[str] = None,
    ) -> InPersonProducts:
        return cast(
            InPersonProducts,
            self.client.get(
                self.path,
                {
                    "ascending": ascending,
                    "limit": limit,
                    "startsAfter": startsAfter,
                },
            ),
        )

    async def get(self, id: str) -> InPersonProduct:
        return cast(InPersonProduct, self.client.get(f"{self.path}/{id}"))
