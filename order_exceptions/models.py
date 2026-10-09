"""Stable domain types for wholesale order exception resolution."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class AcknowledgmentStatus(str, Enum):
    RECEIVED = "received"
    MISSING = "missing"
    UNKNOWN = "unknown"


class ExceptionType(str, Enum):
    MISSING_ACKNOWLEDGMENT = "missing_supplier_acknowledgment"
    DELIVERY_COMMITMENT = "delivery_commitment"
    PRICING_DISCREPANCY = "pricing_discrepancy"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Evidence:
    field: str
    observed: str
    expected: str
    explanation: str


@dataclass(frozen=True)
class Order:
    order_id: str
    tenant_id: str
    supplier_id: str
    acknowledgment_status: AcknowledgmentStatus
    requested_delivery_date: date | None
    committed_delivery_date: date | None
    expected_unit_price: Decimal | None
    quoted_unit_price: Decimal | None
    currency: str


@dataclass(frozen=True)
class OrderException:
    exception_id: str
    order_id: str
    tenant_id: str
    exception_type: ExceptionType
    priority: Priority
    triggering_rule: str
    evidence: tuple[Evidence, ...]
    recommended_action: str
    supplier_draft: str
