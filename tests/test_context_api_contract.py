"""Static contracts for the serverless context and PayPal safety boundaries."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ContextApiContractTests(unittest.TestCase):
    def test_context_api_is_bounded_and_does_not_accept_images(self):
        source = (ROOT / "netlify/functions/context-reason.mts").read_text()
        self.assertIn('request.method !== "POST"', source)
        self.assertIn('raw.length > 16000', source)
        self.assertIn('body.objects', source)
        self.assertIn('slice(0, 12)', source)
        self.assertIn('AbortSignal.timeout(12000)', source)
        self.assertIn('OPENAI_API_KEY', source)
        self.assertIn('AURA_AI_ENABLED', source)
        self.assertIn('frames_received: false', source)
        self.assertIn('raw_images_stored: false', source)
        self.assertIn('windowSize: 60, windowLimit: 30', source)

    def test_paypal_webhook_checks_paypal_signature_before_acknowledging(self):
        source = (ROOT / "netlify/functions/paypal-webhook.mts").read_text()
        self.assertIn('verify-webhook-signature', source)
        self.assertIn('verification_status !== "SUCCESS"', source)
        self.assertIn('PAYPAL_WEBHOOK_ID', source)
        self.assertIn('processed: false', source)
        self.assertIn('request.method !== "POST"', source)

    def test_paypal_order_endpoints_are_rate_limited(self):
        for name in ("paypal-create-order.mts", "paypal-capture-order.mts"):
            source = (ROOT / "netlify/functions" / name).read_text()
            self.assertIn('windowSize: 60, windowLimit: 10', source)

if __name__ == "__main__":
    unittest.main()
