// Payments stay disabled until a durable order ledger, buyer binding, and an
// explicitly provisioned sandbox credential set are configured and tested.
export default async () => Response.json({
  enabled: false,
  clientId: null,
  mode: "sandbox",
  reason: "Checkout is disabled while the payment flow is reviewed."
}, { headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });
