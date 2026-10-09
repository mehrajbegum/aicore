"""Evidence-grounded message drafts; this module never sends messages."""

from .models import ExceptionType, Order


def supplier_follow_up_draft(order: Order, exception_type: ExceptionType) -> str:
    """Create an editable plain-text draft without asserting unknown facts."""
    greeting = f"Hello {order.supplier_id},"
    context = f"We are following up on purchase order {order.order_id}."
    if exception_type is ExceptionType.MISSING_ACKNOWLEDGMENT:
        request = "Please confirm receipt of this order and acknowledge its details."
    elif exception_type is ExceptionType.DELIVERY_COMMITMENT:
        if order.committed_delivery_date is None:
            request = ("Please confirm the delivery date you can commit to. "
                       f"Our requested delivery date is {order.requested_delivery_date.isoformat()}.")
        else:
            request = (f"The committed delivery date we have recorded is {order.committed_delivery_date.isoformat()}, "
                       f"after our requested date of {order.requested_delivery_date.isoformat()}. "
                       "Please confirm whether an earlier date is possible or provide an updated commitment.")
    else:
        request = (f"We have an expected unit price of {order.expected_unit_price} {order.currency} "
                   f"and a quoted unit price of {order.quoted_unit_price} {order.currency}. "
                   "Please review and confirm the correct price.")
    return f"Subject: Follow-up on {order.order_id}\n\n{greeting}\n\n{context} {request}\n\nThank you,"
