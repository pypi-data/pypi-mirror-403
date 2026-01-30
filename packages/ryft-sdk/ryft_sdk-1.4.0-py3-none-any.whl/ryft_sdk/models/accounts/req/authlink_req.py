from __future__ import annotations

from typing_extensions import TypedDict


class CreateAuthLinkReq(TypedDict):
    email: str
    redirectUrl: str
