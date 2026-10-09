"""Pure, deterministic rules for wholesale order exceptions."""

from decimal import Decimal

from .models import AcknowledgmentStatus, Evidence, ExceptionType, Order, OrderException
from .drafting import supplier_follow_up_draft
from .prioritization import action_for, priority_for

# A quote is acceptable when its absolute per-unit difference is at most one cent.
PRICE_TOLERANCE = Decimal("0.01")


def detect_exceptions(orders: list[Order] | tuple[Order, ...]) -> list[OrderException]:
    """Return exceptions in stable order; missing/unknown values do not imply facts."""
    found: list[OrderException] = []
    for order in sorted(orders, key=lambda item: (item.tenant_id, item.order_id)):
        if order.acknowledgment_status is AcknowledgmentStatus.MISSING:
            found.append(_exception(
                order, ExceptionType.MISSING_ACKNOWLEDGMENT, "ACK-001",
                (Evidence("acknowledgment_status", "missing", "received",
                          "The fixture explicitly records that no supplier acknowledgment was received."),),
            ))

        # Compare dates only when the requested date is known.
        if order.requested_delivery_date is not None:
            if order.committed_delivery_date is None and order.acknowledgment_status is AcknowledgmentStatus.RECEIVED:
                found.append(_exception(
                    order, ExceptionType.DELIVERY_COMMITMENT, "DEL-001",
                    (Evidence("committed_delivery_date", "unknown (not provided)",
                              order.requested_delivery_date.isoformat(),
                              "An acknowledgment is recorded, but no delivery commitment date is present."),),
                ))
            elif (order.committed_delivery_date is not None
                  and order.committed_delivery_date > order.requested_delivery_date):
                found.append(_exception(
                    order, ExceptionType.DELIVERY_COMMITMENT, "DEL-002",
                    (Evidence("committed_delivery_date", order.committed_delivery_date.isoformat(),
                              order.requested_delivery_date.isoformat(),
                              "The committed delivery date is later than the requested delivery date."),),
                ))

        if order.expected_unit_price is not None and order.quoted_unit_price is not None:
            difference = abs(order.quoted_unit_price - order.expected_unit_price)
            if difference > PRICE_TOLERANCE:
                found.append(_exception(
                    order, ExceptionType.PRICING_DISCREPANCY, "PRICE-001",
                    (Evidence("quoted_unit_price", str(order.quoted_unit_price),
                              str(order.expected_unit_price),
                              f"Absolute per-unit difference {difference} exceeds tolerance {PRICE_TOLERANCE} {order.currency}."),),
                ))

    rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(found, key=lambda item: (rank[item.priority.value], item.tenant_id,
                                           item.order_id, item.exception_type.value))


def _exception(order: Order, exception_type: ExceptionType, rule: str,
               evidence: tuple[Evidence, ...]) -> OrderException:
    return OrderException(
        exception_id=f"{order.tenant_id}:{order.order_id}:{exception_type.value}",
        order_id=order.order_id,
        tenant_id=order.tenant_id,
        exception_type=exception_type,
        priority=priority_for(exception_type),
        triggering_rule=rule,
        evidence=evidence,
        recommended_action=action_for(exception_type),
        supplier_draft=supplier_follow_up_draft(order, exception_type),
    )
