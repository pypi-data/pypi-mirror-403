from __future__ import annotations

from typing_extensions import TypedDict


class CreateTmpLinkReq(TypedDict):
    url: str
    createdTimestamp: int
    expiresTimestamp: int
