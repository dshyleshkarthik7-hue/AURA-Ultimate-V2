export default async () => {
  const clientId = Netlify.env.get("PAYPAL_CLIENT_ID") ?? "";
  return Response.json({
    enabled: Boolean(clientId),
    clientId: clientId || null,
    mode: "sandbox",
  }, { headers: { "Cache-Control": "no-store" } });
};
