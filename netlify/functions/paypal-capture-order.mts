import { createHmac, timingSafeEqual } from "node:crypto";

const CATALOG: Record<string, { name: string; amount: string }> = {
  "usb-c-hub": { name: "USB-C hub (AURA demo)", amount: "24.00" },
  "hdmi-cable": { name: "HDMI cable (AURA demo)", amount: "9.00" },
  "monitor": { name: "Monitor (AURA demo)", amount: "119.00" },
  "desk": { name: "Desk (AURA demo)", amount: "89.00" },
  "curtain": { name: "Curtain (AURA demo)", amount: "25.00" },
};
function env(name: string): string { return Netlify.env.get(name)?.trim() ?? ""; }
function host(): string { return "https://api-m.sandbox.paypal.com"; }
async function accessToken(): Promise<string> {
  const client = env("PAYPAL_CLIENT_ID"), secret = env("PAYPAL_CLIENT_SECRET");
  if (!client || !secret) throw new Error("PayPal server credentials are not configured");
  const response = await fetch(host() + "/v1/oauth2/token", {
    method: "POST", headers: { Authorization: "Basic " + Buffer.from(client + ":" + secret).toString("base64"),
      "Content-Type": "application/x-www-form-urlencoded" }, body: "grant_type=client_credentials" });
  if (!response.ok) throw new Error("PayPal authentication failed");
  return (await response.json() as { access_token: string }).access_token;
}
function verifyTicket(value: string): { orderId: string; sku: string; amount: string; currency: string; exp: number } {
  const secret = env("AURA_CHECKOUT_SIGNING_SECRET");
  if (secret.length < 32) throw new Error("Checkout signing secret is not configured");
  const [data, signature, extra] = value.split(".");
  if (!data || !signature || extra) throw new Error("Invalid checkout ticket");
  const expected = createHmac("sha256", secret).update(data).digest();
  let actual: Buffer;
  try { actual = Buffer.from(signature, "base64url"); } catch { throw new Error("Invalid checkout ticket"); }
  if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) throw new Error("Invalid checkout ticket");
  const payload = JSON.parse(Buffer.from(data, "base64url").toString("utf8"));
  if (typeof payload.exp !== "number" || payload.exp < Date.now()) throw new Error("Checkout ticket expired");
  return payload;
}

export default async (request: Request) => {
  if (request.method !== "POST") return Response.json({ error: "Method not allowed" }, { status: 405 });
  try {
    const body = await request.json() as { orderId?: string; ticket?: string };
    const proof = verifyTicket(String(body.ticket ?? ""));
    const orderId = String(body.orderId ?? "");
    if (!orderId || orderId !== proof.orderId) return Response.json({ error: "Order/ticket mismatch" }, { status: 400 });
    const item = CATALOG[proof.sku];
    if (!item || proof.amount !== item.amount || proof.currency !== "USD")
      return Response.json({ error: "Order does not match the server catalogue" }, { status: 400 });
    const token = await accessToken();
    const headers = { Authorization: "Bearer " + token, "Content-Type": "application/json" };
    const checkResponse = await fetch(host() + "/v2/checkout/orders/" + encodeURIComponent(orderId), { headers });
    if (!checkResponse.ok) return Response.json({ error: "Could not verify PayPal order" }, { status: 502 });
    const order = await checkResponse.json() as any;
    const unit = order.purchase_units?.[0];
    if (!Array.isArray(order.purchase_units) || order.purchase_units.length !== 1 ||
        !["APPROVED", "COMPLETED"].includes(order.status) || unit?.reference_id !== proof.sku ||
        unit?.amount?.currency_code !== "USD" || unit?.amount?.value !== item.amount) {
      return Response.json({ error: "Order is not approved or its price does not match" }, { status: 409 });
    }
    if (order.status === "COMPLETED") {
      const capture = unit?.payments?.captures?.find((entry: any) => entry.status === "COMPLETED" && entry.amount?.currency_code === "USD" && entry.amount?.value === item.amount);
      if (!capture) return Response.json({ error: "Completed order has no matching completed capture" }, { status: 409 });
      return Response.json({ status: "COMPLETED", orderId, item: item.name, amount: item.amount, currency: "USD" });
    }
    const response = await fetch(host() + "/v2/checkout/orders/" + encodeURIComponent(orderId) + "/capture", {
      method: "POST", headers: { ...headers, "PayPal-Request-Id": "aura-capture-" + orderId.slice(0, 70) }, body: "{}" });
    const result = await response.json() as any;
    if (!response.ok) return Response.json({ error: "PayPal could not capture this order" }, { status: 502 });
    const captureStatus = result.purchase_units?.[0]?.payments?.captures?.[0]?.status;
    if (captureStatus !== "COMPLETED") return Response.json({ error: "Payment capture was not completed", status: captureStatus ?? result.status }, { status: 409 });
    return Response.json({ status: captureStatus, orderId, item: item.name, amount: item.amount, currency: "USD" },
      { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Capture failed";
    const safe = message.includes("ticket") || message.includes("secret") || message.includes("configured") ? message : "Unable to verify/capture this PayPal order";
    return Response.json({ error: safe }, { status: 400 });
  }
};

export const config = { rateLimit: { action: "rate_limit", aggregateBy: "ip", windowSize: 60, windowLimit: 10 } };
