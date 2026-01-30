from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict


class CreateTerminalRequest(TypedDict):
    serialNumber: str
    locationId: str
    name: Optional[str]
    metadata: Optional[dict[str, str]]


class UpdateTerminalRequest(TypedDict):
    locationId: Optional[str]
    name: Optional[str]
    metadata: Optional[dict[str, str]]


class TerminalPaymentRequest(TypedDict):
    amounts: dict[str, Any]
    currency: str
    paymentSession: Optional[dict[str, Any]]
    settings: Optional[dict[str, Any]]


class TerminalRefundRequest(TypedDict):
    paymentSession: dict[str, str]
    amount: Optional[int]
    refundPlatformFee: Optional[bool]
    settings: Optional[dict[str, Any]]


class TerminalConfirmReceiptRequest(TypedDict):
    customerCopy: Optional[dict[str, str]]
    merchantCopy: Optional[dict[str, str]]
