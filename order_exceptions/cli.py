"""Human-readable command-line presentation for the demo."""

import argparse
from pathlib import Path

from .rules import detect_exceptions
from .sample_data import DEFAULT_FIXTURE, FixtureError, load_orders


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect evidence-backed wholesale order exceptions.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE,
                        help="JSON orders fixture (defaults to the included synthetic sample).")
    args = parser.parse_args()
    try:
        orders = load_orders(args.fixture)
    except FixtureError as exc:
        parser.error(str(exc))
    results = detect_exceptions(orders)
    print(f"Loaded {len(orders)} orders; detected {len(results)} exceptions.\n")
    for item in results:
        print(f"[{item.priority.value.upper()}] {item.order_id} - {item.exception_type.value}")
        print(f"  Rule: {item.triggering_rule}")
        for evidence in item.evidence:
            print(f"  Evidence: {evidence.field}: observed={evidence.observed}; expected={evidence.expected}")
            print(f"    {evidence.explanation}")
        print(f"  Next action: {item.recommended_action}\n")
        print("  Editable supplier follow-up draft:")
        for line in item.supplier_draft.splitlines():
            print(f"    {line}")
        print()
    if not results:
        print("No exceptions detected.")
    print("External communication is not enabled in this demo.")
    return 0
