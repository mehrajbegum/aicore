import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from order_exceptions.models import AcknowledgmentStatus, ExceptionType, Order
from order_exceptions.rules import PRICE_TOLERANCE, detect_exceptions
from order_exceptions.sample_data import FixtureError, load_orders


def order(order_id="T-1", **overrides):
    fields = dict(order_id=order_id, tenant_id="tenant-a", supplier_id="supplier-a",
                  acknowledgment_status=AcknowledgmentStatus.RECEIVED,
                  requested_delivery_date=date(2026, 10, 20), committed_delivery_date=date(2026, 10, 20),
                  expected_unit_price=Decimal("10.00"), quoted_unit_price=Decimal("10.00"), currency="USD")
    fields.update(overrides)
    return Order(**fields)


class DetectionTests(unittest.TestCase):
    def test_missing_acknowledgment_detected_only_when_explicitly_missing(self):
        missing = detect_exceptions([order(acknowledgment_status=AcknowledgmentStatus.MISSING)])
        unknown = detect_exceptions([order(acknowledgment_status=AcknowledgmentStatus.UNKNOWN)])
        self.assertEqual([e.exception_type for e in missing], [ExceptionType.MISSING_ACKNOWLEDGMENT])
        self.assertEqual(unknown, [])

    def test_delivery_commitment_missing_and_delayed(self):
        missing = detect_exceptions([order(committed_delivery_date=None)])
        delayed = detect_exceptions([order(committed_delivery_date=date(2026, 10, 21))])
        self.assertEqual([e.triggering_rule for e in missing], ["DEL-001"])
        self.assertEqual([e.triggering_rule for e in delayed], ["DEL-002"])

    def test_delivery_same_date_is_on_time_and_missing_request_is_unknown(self):
        self.assertEqual(detect_exceptions([order()]), [])
        unknown_request = order(requested_delivery_date=None, committed_delivery_date=date(2026, 10, 22))
        self.assertEqual(detect_exceptions([unknown_request]), [])

    def test_price_tolerance_boundary_and_exceedance(self):
        self.assertEqual(PRICE_TOLERANCE, Decimal("0.01"))
        self.assertEqual(detect_exceptions([order(quoted_unit_price=Decimal("10.01"))]), [])
        over = detect_exceptions([order(quoted_unit_price=Decimal("10.02"))])
        self.assertEqual([e.exception_type for e in over], [ExceptionType.PRICING_DISCREPANCY])

    def test_incomplete_price_is_not_a_discrepancy(self):
        self.assertEqual(detect_exceptions([order(quoted_unit_price=None)]), [])
        self.assertEqual(detect_exceptions([order(expected_unit_price=None)]), [])

    def test_results_are_deterministic_and_contain_required_fields(self):
        inputs = [order("B", acknowledgment_status=AcknowledgmentStatus.MISSING),
                  order("A", quoted_unit_price=Decimal("10.02"))]
        first = detect_exceptions(inputs)
        self.assertEqual(first, detect_exceptions(inputs))
        self.assertEqual([item.order_id for item in first], ["B", "A"])
        for item in first:
            self.assertTrue(item.exception_id and item.triggering_rule and item.evidence)
            self.assertTrue(item.recommended_action and item.priority.value)
            self.assertIn(item.order_id, item.supplier_draft)


class FixtureTests(unittest.TestCase):
    def _load_text(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.json"
            path.write_text(text, encoding="utf-8")
            return load_orders(path)

    def test_included_fixture_covers_types_and_boundary_cases(self):
        orders = load_orders()
        results = detect_exceptions(orders)
        self.assertEqual({item.exception_type for item in results}, set(ExceptionType))
        self.assertEqual(sum(1 for item in results if item.order_id == "PO-1004"), 0)
        self.assertEqual(sum(1 for item in results if item.order_id == "PO-1005"), 0)

    def test_malformed_json_and_incomplete_data_have_clear_errors(self):
        with self.assertRaisesRegex(FixtureError, "Invalid JSON"):
            self._load_text("{")
        with self.assertRaisesRegex(FixtureError, "tenant_id is required"):
            self._load_text('[{"order_id":"X"}]')
        incomplete = ('[{"order_id":"X","tenant_id":"T","supplier_id":"S",'
                      '"acknowledgment_status":"unknown","currency":"USD"}]')
        with self.assertRaisesRegex(FixtureError, "requested_delivery_date is required"):
            self._load_text(incomplete)

    def test_invalid_date_and_duplicate_orders_are_rejected(self):
        base = '{"order_id":"X","tenant_id":"T","supplier_id":"S","acknowledgment_status":"received","currency":"USD"'
        with self.assertRaisesRegex(FixtureError, "YYYY-MM-DD"):
            self._load_text("[" + base + ',"requested_delivery_date":"20-10-2026"}]')
        with self.assertRaisesRegex(FixtureError, "Duplicate order_id"):
            self._load_text("[" + base + "}," + base + "}]")


if __name__ == "__main__":
    unittest.main()
