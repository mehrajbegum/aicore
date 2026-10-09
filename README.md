# Side Gig AI Core

A reusable AI operations system.

## Initial workflow
Wholesale Distribution — Order Exception Resolution

## First milestone
Build a synthetic-data demo that detects order exceptions,
collects supporting evidence, recommends next actions,
drafts follow-ups, requires human approval, and tracks resolution.

## Development principles
- Evidence-based recommendations
- Human approval for consequential actions
- Testable workflows and explicit state transitions
- Secure handling of credentials and customer data

## Synthetic wholesale order exception demo

This first vertical slice uses Python's standard library only. Domain records live in `order_exceptions/models.py`; pure detection rules and the priority/action policy are separate from the JSON fixture loader and CLI. The loader validates required identity fields and reports malformed input. Unknown values remain unknown; detection does not treat absent dates or prices as proof of a problem. Each order and exception carries a `tenant_id` as a clean domain boundary, without a tenant service or database.

### Detection rules

- `ACK-001`: detect only an acknowledgment explicitly marked `missing`. `unknown` is not treated as missing.
- `DEL-001`: when acknowledgment is received, the requested date is known, and no commitment date is provided, report a missing delivery commitment.
- `DEL-002`: when both dates are known, report a delay only if the committed date is later than the requested date. A commitment on the requested date is on time. If the requested date is unknown, no comparison is made.
- `PRICE-001`: compare prices only when both are known. The absolute per-unit tolerance is **0.01 in the stated currency**; a difference of exactly 0.01 is accepted, while a greater difference is reported.

Priority is deterministic: acknowledgment and delivery exceptions are high; pricing discrepancies are medium. Each result includes the triggering rule, observed and expected evidence, and a fixed next action. The demo has no AI integration, sender, approval flow, audit log, or persistence; it does not communicate externally.

### Run on Windows

From the repository root, with Python 3.10 or newer installed:

```powershell
py -m order_exceptions
```

To use another JSON fixture:

```powershell
py -m order_exceptions --fixture path\to\orders.json
```

### Run tests

```powershell
py -m unittest discover -s tests -v
```

Each detected item also prints a copyable, editable plain-text supplier draft that uses only the order's known values. It is a presentation template; no sending or approval behavior is included.

Fixture files must include every schema key; use JSON `null` for unavailable dates or prices and `unknown` for unavailable acknowledgment status. This makes incomplete input explicit and produces a validation error when a key is omitted.
