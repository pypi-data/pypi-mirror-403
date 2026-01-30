from __future__ import annotations

from typing import Optional, cast
from ryft_sdk.client import RyftClient
from ryft_sdk.models.deleted_resource_resp import DeletedResourceResp
from ryft_sdk.models.in_person_locations.dto.in_person_locations import (
    InPersonLocation,
    InPersonLocations,
)
from ryft_sdk.models.in_person_locations.req.in_person_locations_req import (
    CreateInPersonLocationRequest,
    UpdateInPersonLocationRequest,
)


class InPersonLocationsClient:
    def __init__(self, client: RyftClient):
        self.client = client
        self.path = "in-person/locations"

    async def create(
        self,
        req: CreateInPersonLocationRequest,
        account: Optional[str] = None,
    ) -> InPersonLocation:
        return cast(
            InPersonLocation,
            self.client.post(self.path, cast(dict, req), account=account),
        )

    async def list(
        self,
        ascending: Optional[bool] = None,
        limit: Optional[int] = None,
        startsAfter: Optional[str] = None,
        account: Optional[str] = None,
    ) -> InPersonLocations:
        return cast(
            InPersonLocations,
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

    async def get(self, id: str, account: Optional[str] = None) -> InPersonLocation:
        return cast(
            InPersonLocation,
            self.client.get(f"{self.path}/{id}", account=account),
        )

    async def update(
        self,
        id: str,
        req: UpdateInPersonLocationRequest,
        account: Optional[str] = None,
    ) -> InPersonLocation:
        return cast(
            InPersonLocation,
            self.client.patch(f"{self.path}/{id}", cast(dict, req), account=account),
        )

    async def delete(
        self, id: str, account: Optional[str] = None
    ) -> DeletedResourceResp:
        return cast(
            DeletedResourceResp,
            self.client.delete(f"{self.path}/{id}", {}, account=account),
        )
