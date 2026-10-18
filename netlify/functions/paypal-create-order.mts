import { randomUUID, createHmac } from "node:crypto";

const CATALOG: Record<string, { name: string; amount: string }> = {
  "usb-c-hub": { name: "USB-C hub (AURA demo)", amount: "24.00" },
  "hdmi-cable": { name: "HDMI cable (AURA demo)", amount: "9.00" },
  "monitor": { name: "Monitor (AURA demo)", amount: "119.00" },
  "desk": { name: "Desk (AURA demo)", amount: "89.00" },
  "curtain": { name: "Curtain (AURA demo)", amount: "25.00" },
};

function env(name: string): string { return Netlify.env.get(name)?.trim() ?? ""; }
function apiHost(): string {
  return env("PAYPAL_MODE").toLowerCase() === "live"
    ? "https://api-m.paypal.com" : "https://api-m.sandbox.paypal.com";
}
async function accessToken(): Promise<string> {
  const client = env("PAYPAL_CLIENT_ID"), secret = env("PAYPAL_CLIENT_SECRET");
  if (!client || !secret) throw new Error("PayPal server credentials are not configured");
  const auth = Buffer.from(client + ":" + secret).toString("base64");
  const response = await fetch(apiHost() + "/v1/oauth2/token", {
    method: "POST",
    headers: { Authorization: "Basic " + auth, "Content-Type": "application/x-www-form-urlencoded" },
    body: "grant_type=client_credentials",
  });
  if (!response.ok) throw new Error("PayPal authentication failed");
  return (await response.json() as { access_token: string }).access_token;
}
function ticket(payload: object): string {
  const secret = env("AURA_CHECKOUT_SIGNING_SECRET");
  if (secret.length < 32) throw new Error("Set AURA_CHECKOUT_SIGNING_SECRET to a random secret of at least 32 characters");
  const data = Buffer.from(JSON.stringify(payload)).toString("base64url");
  const sig = createHmac("sha256", secret).update(data).digest("base64url");
  return data + "." + sig;
}

export default async (request: Request) => {
  if (request.method !== "POST") return Response.json({ error: "Method not allowed" }, { status: 405 });
  try {
    const body = await request.json() as { sku?: string };
    const sku = String(body.sku ?? "");
    const item = CATALOG[sku];
    if (!item) return Response.json({ error: "Unknown demo product" }, { status: 400 });
    if (env("AURA_CHECKOUT_SIGNING_SECRET").length < 32) throw new Error("Set AURA_CHECKOUT_SIGNING_SECRET to a random secret of at least 32 characters");
    const token = await accessToken();
    const response = await fetch(apiHost() + "/v2/checkout/orders", {
      method: "POST",
      headers: { Authorization: "Bearer " + token, "Content-Type": "application/json",
        "PayPal-Request-Id": randomUUID(), Prefer: "return=representation" },
      body: JSON.stringify({
        intent: "CAPTURE",
        purchase_units: [{ reference_id: sku, description: item.name,
          amount: { currency_code: "USD", value: item.amount } }],
        application_context: { brand_name: "AURA Context Intelligence", shipping_preference: "NO_SHIPPING",
          user_action: "PAY_NOW" },
      }),
    });
    const data = await response.json() as { id?: string; message?: string; name?: string };
    if (!response.ok || !data.id) return Response.json({ error: "PayPal could not create the order" }, { status: 502 });
    const checkoutTicket = ticket({ orderId: data.id, sku, amount: item.amount,
      currency: "USD", exp: Date.now() + 30 * 60 * 1000 });
    return Response.json({ id: data.id, ticket: checkoutTicket, item: item.name, amount: item.amount, currency: "USD" },
      { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Checkout setup failed";
    const safe = message.includes("not configured") || message.includes("AURA_CHECKOUT") ? message : "Unable to start PayPal checkout";
    return Response.json({ error: safe }, { status: 503 });
  }
};

export const config = { rateLimit: { action: "rate_limit", aggregateBy: "ip", windowSize: 60, windowLimit: 10 } };
