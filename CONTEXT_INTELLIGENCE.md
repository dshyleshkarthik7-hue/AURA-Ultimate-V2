# AURA Context Intelligence + PayPal Checkout

This branch adds a conservative relationship-reasoning layer to the existing AURA perception project. The existing camera/classifier proposes labels; this module turns labels into object twins, a context graph, missing-information questions, and inspectable recommendations.

## Included
- aura/context_intelligence.py: dependency-free graph model and rule-based reasoning for compatibility, fit/space, scene understanding, and commerce intent.
- Detection confidence is preserved. Unknown labels are skipped; uncertain labels are surfaced.
- The sample catalogue is tiny and illustrative. Exact models, ports, and dimensions are requested when evidence is insufficient.
- aura/paypal_checkout.py: server-side PayPal Orders v2 helper. Sandbox is default; credentials are read only from environment variables.
- tests/test_context_intelligence.py: unit tests.

## Tests
Run: python -m unittest discover -s tests -p "test*.py"

## Example
from aura.context_intelligence import reason_about_scene
result = reason_about_scene(
    [{"label": "Laptop", "confidence": 0.92}, {"label": "Monitor", "confidence": 0.88}],
    question="Can I connect this monitor?",
)
print(result["summary"], result["missing_information"])

Call the engine after PerceptionEngine.predict() and pass only labels/confidences. Camera frames are not sent to this module.

## PayPal Sandbox
Set server environment variables PAYPAL_MODE=sandbox, PAYPAL_CLIENT_ID, and PAYPAL_CLIENT_SECRET. Never place credentials in browser code or commit them.

create_order() creates a USD order using a server-defined price. After a buyer approves through a properly implemented PayPal JS SDK flow, capture_order(order_id) may be called. Do not expose capture without validating the expected amount, currency, merchant, and session/user ownership. This helper is not a complete web checkout: production also needs order persistence, idempotency, webhook verification, rate limiting, and secure logging.

## Honest scope
This is a rule-based MVP, not a general LLM and not proof of physical fit, electrical compatibility, or accessibility safety. The catalogue is not a live store listing. No PayPal payment was performed by adding these files. A hackathon-ready buyer flow still needs a UI, PayPal JS SDK approval flow, Sandbox end-to-end testing, and a demo recording.
