from __future__ import annotations

from typing import Optional, cast
from ryft_sdk.client import RyftClient
from ryft_sdk.models.deleted_resource_resp import DeletedResourceResp
from ryft_sdk.models.in_person_terminals.dto.in_person_terminals import (
    Terminal,
    Terminals,
)
from ryft_sdk.models.in_person_terminals.req.in_person_terminals_req import (
    CreateTerminalRequest,
    UpdateTerminalRequest,
    TerminalPaymentRequest,
    TerminalRefundRequest,
    TerminalConfirmReceiptRequest,
)


class InPersonTerminalsClient:
    def __init__(self, client: RyftClient):
        self.client = client
        self.path = "in-person/terminals"

    async def create(
        self, req: CreateTerminalRequest, account: Optional[str] = None
    ) -> Terminal:
        return cast(
            Terminal, self.client.post(self.path, cast(dict, req), account=account)
        )

    async def list(
        self,
        ascending: Optional[bool] = None,
        limit: Optional[int] = None,
        startsAfter: Optional[str] = None,
        account: Optional[str] = None,
    ) -> Terminals:
        return cast(
            Terminals,
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

    async def get(self, id: str, account: Optional[str] = None) -> Terminal:
        return cast(Terminal, self.client.get(f"{self.path}/{id}", account=account))

    async def update(
        self, id: str, req: UpdateTerminalRequest, account: Optional[str] = None
    ) -> Terminal:
        return cast(
            Terminal,
            self.client.patch(f"{self.path}/{id}", cast(dict, req), account=account),
        )

    async def delete(
        self, id: str, account: Optional[str] = None
    ) -> DeletedResourceResp:
        return cast(
            DeletedResourceResp,
            self.client.delete(f"{self.path}/{id}", {}, account=account),
        )

    async def init_payment(
        self, id: str, req: TerminalPaymentRequest, account: Optional[str] = None
    ) -> Terminal:
        return cast(
            Terminal,
            self.client.post(
                f"{self.path}/{id}/payment", cast(dict, req), account=account
            ),
        )

    async def init_refund(
        self, id: str, req: TerminalRefundRequest, account: Optional[str] = None
    ) -> Terminal:
        return cast(
            Terminal,
            self.client.post(
                f"{self.path}/{id}/refund", cast(dict, req), account=account
            ),
        )

    async def cancel_action(self, id: str, account: Optional[str] = None) -> Terminal:
        return cast(
            Terminal,
            self.client.post(f"{self.path}/{id}/cancel-action", {}, account=account),
        )

    async def confirm_receipt(
        self, id: str, req: TerminalConfirmReceiptRequest, account: Optional[str] = None
    ) -> Terminal:
        return cast(
            Terminal,
            self.client.post(
                f"{self.path}/{id}/confirm-receipt", cast(dict, req), account=account
            ),
        )
