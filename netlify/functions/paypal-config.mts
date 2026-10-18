export default async () => {
  const clientId = Netlify.env.get("PAYPAL_CLIENT_ID") ?? "";
  return Response.json({
    enabled: Boolean(clientId),
    clientId: clientId || null,
    mode: (Netlify.env.get("PAYPAL_MODE") ?? "sandbox").toLowerCase() === "live" ? "live" : "sandbox",
  }, { headers: { "Cache-Control": "no-store" } });
};
