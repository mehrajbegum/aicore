"""Deterministic priority and action policy for detected exceptions."""

from .models import ExceptionType, Priority


PRIORITIES = {
    ExceptionType.MISSING_ACKNOWLEDGMENT: Priority.HIGH,
    ExceptionType.DELIVERY_COMMITMENT: Priority.HIGH,
    ExceptionType.PRICING_DISCREPANCY: Priority.MEDIUM,
}

RECOMMENDED_ACTIONS = {
    ExceptionType.MISSING_ACKNOWLEDGMENT: "Request supplier acknowledgment and confirm the order was received.",
    ExceptionType.DELIVERY_COMMITMENT: "Ask the supplier to confirm a delivery date that meets the requested date.",
    ExceptionType.PRICING_DISCREPANCY: "Review the quoted price against the expected price and request clarification.",
}


def priority_for(exception_type: ExceptionType) -> Priority:
    return PRIORITIES[exception_type]


def action_for(exception_type: ExceptionType) -> str:
    return RECOMMENDED_ACTIONS[exception_type]
