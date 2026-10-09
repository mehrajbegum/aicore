"""Strict JSON fixture loader with actionable validation errors."""

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .models import AcknowledgmentStatus, Order


class FixtureError(ValueError):
    """Raised when fixture data is unreadable or violates the order schema."""


DEFAULT_FIXTURE = Path(__file__).with_name("fixtures") / "sample_orders.json"


def load_orders(path: str | Path = DEFAULT_FIXTURE) -> list[Order]:
    fixture = Path(path)
    try:
        raw = json.loads(fixture.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FixtureError(f"Cannot read fixture '{fixture}': {exc}") from exc
    except UnicodeError as exc:
        raise FixtureError(f"Fixture '{fixture}' must be valid UTF-8 JSON.") from exc
    except json.JSONDecodeError as exc:
        raise FixtureError(f"Invalid JSON in '{fixture}' at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc

    if not isinstance(raw, list):
        raise FixtureError("Fixture root must be a JSON array of orders.")
    orders = [_parse_order(item, index) for index, item in enumerate(raw)]
    seen: set[tuple[str, str]] = set()
    for order in orders:
        key = (order.tenant_id, order.order_id)
        if key in seen:
            raise FixtureError(f"Duplicate order_id '{order.order_id}' for tenant '{order.tenant_id}'.")
        seen.add(key)
    return orders


def _parse_order(item: Any, index: int) -> Order:
    label = f"orders[{index}]"
    if not isinstance(item, dict):
        raise FixtureError(f"{label} must be a JSON object.")
    required = (
        "order_id", "tenant_id", "supplier_id", "acknowledgment_status", "currency",
        "requested_delivery_date", "committed_delivery_date",
        "expected_unit_price", "quoted_unit_price",
    )
    for key in required:
        if key not in item:
            raise FixtureError(f"{label}.{key} is required; use null or 'unknown' when a value is unavailable.")
        if not isinstance(item[key], str) or not item[key].strip():
            raise FixtureError(f"{label}.{key} must be a non-empty string.")
    try:
        acknowledgment = AcknowledgmentStatus(item["acknowledgment_status"])
    except ValueError as exc:
        raise FixtureError(f"{label}.acknowledgment_status must be received, missing, or unknown.") from exc
    return Order(
        order_id=item["order_id"], tenant_id=item["tenant_id"], supplier_id=item["supplier_id"],
        acknowledgment_status=acknowledgment,
        requested_delivery_date=_date(item, "requested_delivery_date", label),
        committed_delivery_date=_date(item, "committed_delivery_date", label),
        expected_unit_price=_decimal(item, "expected_unit_price", label),
        quoted_unit_price=_decimal(item, "quoted_unit_price", label), currency=item["currency"],
    )


def _date(item: dict[str, Any], key: str, label: str) -> date | None:
    value = item.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise FixtureError(f"{label}.{key} must be an ISO date string or null.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise FixtureError(f"{label}.{key} must use YYYY-MM-DD format.") from exc


def _decimal(item: dict[str, Any], key: str, label: str) -> Decimal | None:
    value = item.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise FixtureError(f"{label}.{key} must be a decimal string or null.")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise FixtureError(f"{label}.{key} must be a valid decimal string.") from exc
    if not result.is_finite() or result < 0:
        raise FixtureError(f"{label}.{key} must be a finite, non-negative amount.")
    return result
