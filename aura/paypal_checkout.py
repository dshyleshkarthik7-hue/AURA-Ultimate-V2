"""Server-side PayPal Orders v2 helper. Sandbox is the default."""
from __future__ import annotations
import base64, json, os, urllib.error, urllib.request
from decimal import Decimal, InvalidOperation

class PayPalError(RuntimeError):
    pass

def _settings():
    client = os.getenv("PAYPAL_CLIENT_ID", "").strip()
    secret = os.getenv("PAYPAL_CLIENT_SECRET", "").strip()
    mode = os.getenv("PAYPAL_MODE", "sandbox").strip().lower()
    if mode not in {"sandbox", "live"}:
        raise PayPalError("PAYPAL_MODE must be sandbox or live")
    if not client or not secret:
        raise PayPalError("Set PayPal credentials in server environment variables")
    host = "https://api-m.sandbox.paypal.com" if mode == "sandbox" else "https://api-m.paypal.com"
    return client, secret, host

def _api(method: str, path: str, payload=None, request_id=None):
    client, secret, host = _settings()
    auth = base64.b64encode(f"{client}:{secret}".encode()).decode()
    req = urllib.request.Request(host + "/v1/oauth2/token", data=b"grant_type=client_credentials",
        headers={"Authorization": "Basic " + auth, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            token = json.loads(response.read().decode())["access_token"]
        headers = {"Authorization": "Bearer " + token, "Accept": "application/json", "Content-Type": "application/json"}
        if request_id:
            headers["PayPal-Request-Id"] = str(request_id)[:108]
        body = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(host + path, data=body, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise PayPalError(f"PayPal returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, KeyError) as exc:
        raise PayPalError("PayPal request failed; check network and Sandbox credentials.") from exc

def create_order(*, item_name: str, amount: str, currency: str = "USD", request_id: str) -> dict:
    """Create a fixed-price order. Never accept browser-submitted price as authority."""
    try:
        value = Decimal(amount).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("amount must be a decimal amount") from exc
    if value <= 0 or value > Decimal("10000.00"):
        raise ValueError("amount must be between 0.01 and 10000.00")
    if currency != "USD":
        raise ValueError("This demo supports USD only; do not silently convert currencies")
    name = " ".join(str(item_name).split())[:127]
    if not name:
        raise ValueError("item_name is required")
    return _api("POST", "/v2/checkout/orders", {"intent": "CAPTURE", "purchase_units": [{
        "reference_id": "aura-demo-item", "description": name,
        "amount": {"currency_code": currency, "value": f"{value:.2f}"}}],
        "application_context": {"brand_name": "AURA Context Intelligence", "shipping_preference": "NO_SHIPPING"}},
        request_id=request_id)

def capture_order(order_id: str) -> dict:
    """Capture only after server verifies amount, currency, merchant, and session ownership."""
    order_id = str(order_id).strip()
    if not order_id or len(order_id) > 64 or not order_id.replace("-", "").isalnum():
        raise ValueError("Invalid PayPal order ID")
    return _api("POST", f"/v2/checkout/orders/{order_id}/capture", {})
