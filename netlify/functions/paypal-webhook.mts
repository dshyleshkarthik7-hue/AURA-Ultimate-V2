function env(name: string): string { return Netlify.env.get(name)?.trim() ?? ""; }
function apiHost(): string {
  return env("PAYPAL_MODE").toLowerCase() === "live" ? "https://api-m.paypal.com" : "https://api-m.sandbox.paypal.com";
}
async function token(): Promise<string> {
  const client = env("PAYPAL_CLIENT_ID"), secret = env("PAYPAL_CLIENT_SECRET");
  if (!client || !secret) throw new Error("PayPal server credentials are not configured");
  const response = await fetch(apiHost() + "/v1/oauth2/token", {
    method: "POST",
    headers: { Authorization: "Basic " + Buffer.from(client + ":" + secret).toString("base64"), "Content-Type": "application/x-www-form-urlencoded" },
    body: "grant_type=client_credentials",
    signal: AbortSignal.timeout(10000)
  });
  if (!response.ok) throw new Error("PayPal authentication failed");
  return (await response.json() as { access_token: string }).access_token;
}
const safeJson = (body: unknown, status = 200) => Response.json(body, { status, headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });

export default async (request: Request) => {
  if (request.method !== "POST") return safeJson({ error: "Method not allowed" }, 405);
  if (!(request.headers.get("content-type") || "").toLowerCase().includes("application/json")) return safeJson({ error: "Expected application/json" }, 415);
  try {
    const raw = await request.text();
    if (raw.length > 128000) return safeJson({ error: "Webhook body too large" }, 413);
    const event = JSON.parse(raw) as { id?: string; event_type?: string };
    const webhookId = env("PAYPAL_WEBHOOK_ID");
    if (!webhookId) return safeJson({ error: "PAYPAL_WEBHOOK_ID is not configured" }, 503);
    const headers = {
      auth_algo: request.headers.get("paypal-auth-algo"),
      cert_url: request.headers.get("paypal-cert-url"),
      transmission_id: request.headers.get("paypal-transmission-id"),
      transmission_sig: request.headers.get("paypal-transmission-sig"),
      transmission_time: request.headers.get("paypal-transmission-time")
    };
    if (Object.values(headers).some(value => !value) || !event.id || !event.event_type) {
      return safeJson({ error: "Missing PayPal signature headers or event identity" }, 400);
    }
    const access = await token();
    const verify = await fetch(apiHost() + "/v1/notifications/verify-webhook-signature", {
      method: "POST",
      headers: { Authorization: "Bearer " + access, "Content-Type": "application/json" },
      body: JSON.stringify({ ...headers, webhook_id: webhookId, webhook_event: event }),
      signal: AbortSignal.timeout(10000)
    });
    if (!verify.ok) return safeJson({ error: "PayPal signature verification service failed" }, 502);
    const result = await verify.json() as { verification_status?: string };
    if (result.verification_status !== "SUCCESS") return safeJson({ error: "Webhook signature is invalid" }, 400);
    // This endpoint intentionally performs no fulfilment. A durable, idempotent order
    // ledger must be connected before verified events can trigger business side effects.
    return safeJson({ received: true, verified: true, eventId: event.id, eventType: event.event_type, processed: false });
  } catch {
    return safeJson({ error: "Unable to verify webhook" }, 400);
  }
};
