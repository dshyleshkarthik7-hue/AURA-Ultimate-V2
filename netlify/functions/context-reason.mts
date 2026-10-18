import { randomUUID } from "node:crypto";

type SceneObject = { id: string; label: string; confidence: number; source: string; attributes: Record<string, unknown> };
type Edge = { subject: string; predicate: string; object: string; confidence: number; evidence: string; status: "inferred" | "needs_verification" };
const CATALOG: Record<string, { ports?: string[]; priceUsd: number; dimensionsCm?: { width?: number; depth?: number; height?: number }; notes: string }> = {
  laptop: { ports: ["USB-C", "HDMI"], priceUsd: 499, notes: "Generic illustrative device; ports vary by model." },
  monitor: { ports: ["HDMI", "DisplayPort"], priceUsd: 119, notes: "Generic illustrative device; ports vary by model." },
  "usb-c hub": { ports: ["USB-C", "HDMI", "USB-A"], priceUsd: 24, notes: "USB-C video output depends on the host device." },
  "hdmi cable": { ports: ["HDMI"], priceUsd: 9, notes: "Cable version and length are not verified." },
  desk: { dimensionsCm: { width: 120, depth: 60 }, priceUsd: 89, notes: "Example dimensions only; verify a real listing." },
  curtain: { priceUsd: 25, notes: "Measure the window and mounting style before choosing a size." },
  "steel glass": { priceUsd: 8, notes: "AURA's trained class; material/food safety is not certified by visual recognition." },
  "steel water bottle": { priceUsd: 15, notes: "AURA's trained class; capacity and material are not certified by visual recognition." },
  "bottle gourd": { priceUsd: 4, notes: "AURA's trained class; visual recognition is not food-safety advice." }
};
const normal = (value: unknown) => String(value ?? "").trim().toLowerCase().replace(/[_-]+/g, " ").replace(/\s+/g, " ").slice(0, 100);
const words = (value: string) => value.toLowerCase();
const json = (body: unknown, status = 200) => Response.json(body, { status, headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });

function sanitizeObjects(input: unknown): SceneObject[] {
  if (!Array.isArray(input)) return [];
  const out: SceneObject[] = [];
  for (const raw of input.slice(0, 12)) {
    if (!raw || typeof raw !== "object") continue;
    const row = raw as Record<string, unknown>;
    const label = normal(row.label);
    if (!label || label === "unknown") continue;
    const rawConfidence = Number(row.confidence ?? 0.6);
    const confidence = Number.isFinite(rawConfidence) ? Math.max(0, Math.min(1, rawConfidence)) : 0.5;
    const attributes: Record<string, unknown> = {};
    if (row.attributes && typeof row.attributes === "object" && !Array.isArray(row.attributes)) {
      for (const [key, value] of Object.entries(row.attributes as Record<string, unknown>).slice(0, 12)) {
        if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") attributes[key.slice(0, 40)] = String(value).slice(0, 120);
      }
    }
    out.push({ id: String(row.id ?? "object-" + (out.length + 1)).replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 48) || "object-" + (out.length + 1),
      label, confidence, source: row.source === "aura perception" || row.source === "aura_perception_engine" ? "aura perception" : "user supplied", attributes });
  }
  return out.filter((o, i, all) => all.findIndex(x => x.label === o.label) === i);
}

function reason(objects: SceneObject[], question: string, constraints: Record<string, unknown>) {
  const q = words(question), labels = objects.map(o => o.label), relations: Edge[] = [], observations: string[] = [], missing: string[] = [], recommendations: Array<Record<string, unknown>> = [];
  let intent = "understand_scene";
  const object = (label: string) => objects.find(o => o.label === label);
  if (!objects.length) {
    return { intent, summary: "I don't have an object label to reason about yet. Start AURA perception or enter labels manually.", graph: { objects, relations }, observations, missing_information: ["one or more object labels"], recommendations, confidence: 0, limitations: ["No reliable object labels were supplied."] };
  }
  if (/(connect|plug|port|monitor|display|compatible|compatib|hdmi|usb-c)/.test(q)) {
    intent = "compatibility";
    const laptop = object("laptop"), monitor = object("monitor"), hub = object("usb-c hub"), cable = object("hdmi cable");
    if (laptop && monitor) {
      const shared = (CATALOG.laptop.ports ?? []).filter(port => (CATALOG.monitor.ports ?? []).includes(port));
      relations.push({ subject: laptop.id, predicate: "may_connect_to", object: monitor.id, confidence: 0.55, evidence: "Generic illustrative port catalogue only; exact models and ports are unverified.", status: "needs_verification" });
      observations.push("The example catalogue lists a shared port type: " + shared.join(", ") + ". This is not confirmation for your specific devices.");
      missing.push("Exact laptop and monitor model numbers and a check of their physical ports");
    } else {
      observations.push("The current labels do not establish a connection path.");
      missing.push("Identify both devices and provide exact model numbers or port details");
    }
    if (hub) recommendations.push({ item: "USB-C hub", reason: "Consider only if the host supports the required video mode over USB-C.", sku: "usb-c-hub", price_usd: CATALOG["usb-c hub"].priceUsd, price_is_illustrative: true });
    if (cable) recommendations.push({ item: "HDMI cable", reason: "Verify both devices have HDMI and check the required cable version and length.", sku: "hdmi-cable", price_usd: CATALOG["hdmi cable"].priceUsd, price_is_illustrative: true });
    if (!missing.length) missing.push("Verify the exact specifications before buying adapters or cables");
  } else if (/(fit|room|width|measure|curtain|desk|space|dimension|size)/.test(q)) {
    intent = "fit_and_space";
    const roomWidth = Number(constraints.available_width_cm), productWidth = Number(constraints.product_width_cm);
    if (Number.isFinite(roomWidth) && roomWidth > 0 && Number.isFinite(productWidth) && productWidth > 0) {
      const fits = productWidth <= roomWidth;
      observations.push("Entered widths: product " + productWidth + " cm; available space " + roomWidth + " cm.");
      relations.push({ subject: object("desk")?.id ?? objects[0].id, predicate: fits ? "fits_entered_width" : "exceeds_entered_width", object: objects[0].id, confidence: 0.9, evidence: "Arithmetic using user-entered widths only; depth, clearance and measurement accuracy are not checked.", status: "needs_verification" });
      if (!fits) recommendations.push({ item: "Re-measure or choose a narrower item", reason: "The entered product width exceeds the entered available width." });
    } else missing.push("Available width and product width in centimetres (and depth/clearance where relevant)");
    observations.push("Camera pixels do not provide reliable physical dimensions without a calibrated reference.");
    if (labels.includes("curtain")) missing.push("Window width/drop, mounting type, and desired fullness");
    if (labels.includes("desk")) missing.push("Desk width/depth, walking clearance, and doorway route");
  } else if (/(buy|purchase|price|order|shop|recommend|recommendation)/.test(q)) {
    intent = "commerce";
    observations.push("The catalogue is a small illustrative fixture, not live inventory or a verified offer.");
    missing.push("Confirm exact product, budget, delivery region, specifications, and return policy");
    for (const label of labels) {
      const item = CATALOG[label];
      if (item) recommendations.push({ item: label, price_usd: item.priceUsd, price_is_illustrative: true, reason: item.notes });
    }
  } else {
    observations.push("Object labels supplied: " + labels.join(", ") + ".");
    missing.push("Ask a specific question about a relationship, fit, connection, or next step");
  }
  const confidence = objects.reduce((sum, o) => sum + o.confidence, 0) / objects.length;
  const summary = [...observations, ...recommendations.map(r => String(r.reason)), ...(missing.length ? ["Still needed: " + [...new Set(missing)].join("; ") + "."] : [])].join(" ");
  return { intent, summary, graph: { objects, relations }, observations, missing_information: [...new Set(missing)], recommendations, confidence: Math.round(confidence * 1000) / 1000,
    limitations: ["Relations are hypotheses, not certifications or guarantees.", "Catalogue prices/specifications are illustrative and not live offers.", "AURA does not infer precise physical dimensions from uncalibrated camera images."] };
}

async function conversationalize(base: ReturnType<typeof reason>, question: string, language: string) {
  const key = Netlify.env.get("OPENAI_API_KEY")?.trim();
  if (!key || Netlify.env.get("AURA_AI_ENABLED")?.toLowerCase() === "false") return { ...base, answer: base.summary, follow_up_questions: base.missing_information.slice(0, 3), ai_used: false };
  const model = (Netlify.env.get("AURA_AI_MODEL") || "gpt-4o-mini").trim().slice(0, 80);
  try {
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST", headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
      signal: AbortSignal.timeout(12000),
      body: JSON.stringify({ model, temperature: 0.2, response_format: { type: "json_object" },
        messages: [
          { role: "system", content: "You are AURA, a cautious multilingual context assistant. Return JSON only with keys answer (string) and follow_up_questions (array of short strings). Answer in the requested language. Use only facts and limitations in the supplied structured result. Never invent model specifications, prices, measurements, compatibility, safety or availability. Clearly state uncertainty. Do not suggest a purchase when required evidence is missing. Do not ask for sensitive personal data. You receive text only; never claim to have inspected an image." },
          { role: "user", content: JSON.stringify({ language, question, evidence: base }) }
        ] })
    });
    if (!response.ok) return { ...base, answer: base.summary, follow_up_questions: base.missing_information.slice(0, 3), ai_used: false };
    const data = await response.json() as any;
    const text = data.choices?.[0]?.message?.content;
    if (typeof text !== "string" || text.length > 5000) throw new Error("Invalid assistant response");
    const parsed = JSON.parse(text);
    const answer = typeof parsed.answer === "string" ? parsed.answer.slice(0, 2500) : base.summary;
    const follow = Array.isArray(parsed.follow_up_questions) ? parsed.follow_up_questions.filter((x: unknown) => typeof x === "string").slice(0, 4).map((x: string) => x.slice(0, 180)) : base.missing_information.slice(0, 3);
    return { ...base, answer, follow_up_questions: follow, ai_used: true };
  } catch {
    return { ...base, answer: base.summary, follow_up_questions: base.missing_information.slice(0, 3), ai_used: false };
  }
}

export default async (request: Request) => {
  if (request.method !== "POST") return json({ error: "Method not allowed" }, 405);
  const type = request.headers.get("content-type") || "";
  if (!type.toLowerCase().includes("application/json")) return json({ error: "Send application/json" }, 415);
  try {
    const raw = await request.text();
    if (raw.length > 16000) return json({ error: "Request is too large" }, 413);
    const body = JSON.parse(raw) as Record<string, unknown>;
    const question = String(body.question ?? "").trim().slice(0, 500);
    const language = String(body.language ?? "en-IN").slice(0, 20);
    const allowedLanguages = new Set(["en-IN", "hi-IN", "te-IN", "ta-IN", "gu-IN"]);
    const constraints = body.constraints && typeof body.constraints === "object" && !Array.isArray(body.constraints) ? body.constraints as Record<string, unknown> : {};
    const cleanConstraints: Record<string, unknown> = {};
    for (const key of ["available_width_cm", "product_width_cm", "available_depth_cm", "product_depth_cm", "budget_usd", "device_model"]) {
      const value = constraints[key];
      if (typeof value === "number" && Number.isFinite(value)) cleanConstraints[key] = Math.max(0, Math.min(100000, value));
      else if (typeof value === "string") cleanConstraints[key] = value.slice(0, 120);
    }
    const objects = sanitizeObjects(body.objects);
    const base = reason(objects, question, cleanConstraints);
    const result = await conversationalize(base, question, allowedLanguages.has(language) ? language : "en-IN");
    return json({ ...result, request_id: randomUUID(), privacy: { frames_received: false, raw_images_stored: false, text_sent_to_optional_ai: result.ai_used } });
  } catch {
    return json({ error: "Invalid request. Send a valid JSON object with object labels and a question." }, 400);
  }
};

export const config = { rateLimit: { action: "rate_limit", aggregateBy: "ip", windowSize: 60, windowLimit: 30 } };
