# Netlify deployment and checkout operations

## Deploy the app
Set the Netlify build publish directory to `web` (already in `netlify.toml`) and install the dependencies from the root `package.json`. Netlify Functions are in `netlify/functions/`.

## Sandbox checkout prerequisites
Configure these as **Netlify environment variables with Functions scope**:
- `PAYPAL_MODE=sandbox` (live mode is intentionally not supported by this demo)
- `PAYPAL_CLIENT_ID` — Sandbox REST app client ID
- `PAYPAL_CLIENT_SECRET` — Sandbox REST app secret
- `AURA_CHECKOUT_SIGNING_SECRET` — randomly generated secret, at least 32 characters
- `PAYPAL_WEBHOOK_ID` — webhook ID for the Sandbox REST app (required for webhook verification)

Enable Netlify Database for this site. The SQL migration under `netlify/database/migrations/` creates the durable order ledger, event-id deduplication, and per-session rate-limit table. Deploy after provisioning the database and setting environment variables.

Use a buyer test account from the PayPal Developer Dashboard. Never use real payment credentials for a demo. The functions deliberately use the Sandbox API only.

## Endpoints
- `GET /.netlify/functions/paypal-config`: public client ID and creates a random HttpOnly checkout session cookie.
- `POST /.netlify/functions/paypal-create-order`: accepts a server allowlisted SKU, rate limits the session, creates a PayPal order and stores it in the ledger.
- `POST /.netlify/functions/paypal-capture-order`: validates the HMAC ticket, session ownership, stored order, and PayPal's current order amount/currency/SKU before capture.
- `GET /.netlify/functions/paypal-orders`: returns only the current browser session's recent order summaries.
- `POST /.netlify/functions/paypal-webhook`: verifies PayPal's webhook signature using PayPal's verification API, deduplicates event IDs, and reconciles completed captures into the ledger.

## Important limits
This is still a hackathon/demo commerce integration, not a ready-to-sell production store. The catalogue is test data and uses `NO_SHIPPING`; no goods are fulfilled. Before live commerce, add merchant/product onboarding, verified live inventory/prices, tax and shipping rules, a support/refund flow, monitoring/alerts, operational access controls, and a security review. Do not change the code to live mode for a demo.
