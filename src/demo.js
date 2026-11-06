// Demos web sin instalación (/api/demo/<slug>). Llaman al MCP real con la licencia interna del hub (HUB_DEMO_LICENSE):
// el visitante no paga nada. Herramienta y argumentos fijos por servidor; entradas pequeñas; límite por IP y día en D1.

import { clientIp, giveBack, hash, num, take, today } from "./limits.js";

const TARGETS = new Set(["a3", "contaplus_csv", "xero_csv", "quickbooks_csv"]);

export const DEMOS = {
  "web-intel": {
    tool: "read_url",
    args(input) {
      const raw = String(input.url || "").trim();
      if (raw.length > 500) throw new Error("La URL es demasiado larga.");
      if (/^[a-z][a-z0-9+.-]*:/i.test(raw) && !/^https?:\/\//i.test(raw)) throw new Error("Solo URLs http o https.");
      let u;
      try { u = new URL(/^https?:\/\//i.test(raw) ? raw : "https://" + raw); } catch (e) { throw new Error("Escribe una URL válida."); }
      if (u.protocol !== "https:" && u.protocol !== "http:") throw new Error("Solo URLs http o https.");
      if (u.username || u.password) throw new Error("La URL no puede llevar usuario ni contraseña.");
      return { url: u.toString(), max_chars: 6000 };
    },
    view(d) {
      return { url: d.url, title: d.title, word_count: d.word_count, truncated: !!d.truncated, markdown: String(d.markdown || "").slice(0, 6000) };
    },
  },
  norma43: {
    tool: "parse_norma43",
    args(input) {
      const content = String(input.content || "");
      if (!content.trim()) throw new Error("Pega un extracto Norma 43.");
      if (content.length > 20_000) throw new Error("La demo admite extractos de hasta 20 KB. Instala el servidor para ficheros grandes.");
      return { content, include_movements: true };
    },
    view(d) {
      const accounts = (d.accounts || []).slice(0, 3).map((a) => ({
        iban: a.iban_formatted || a.iban || a.ccc, bank: a.bank_name || null, holder: a.holder || null, currency: a.currency,
        period: a.period || null,
        opening_balance: a.opening_balance, closing_balance: a.closing_balance,
        movements: (a.movements || []).slice(0, 25).map((m) => ({
          date: m.operation_date, amount: m.amount, direction: m.direction, description: m.description,
          concept: m.common_concept && m.common_concept.name,
        })),
      }));
      return { valid: !!d.valid, summary: d.summary || {}, issues: (d.issues || []).slice(0, 10), accounts };
    },
  },
  contabridge: {
    tool: "convert_journal",
    args(input) {
      const content = String(input.content || "");
      if (!content.trim()) throw new Error("Pega unos asientos en CSV.");
      if (content.length > 5_000 || content.split("\n").length > 40) throw new Error("La demo admite hasta 40 líneas. Instala el servidor para diarios completos.");
      const target = String(input.target || "a3");
      if (!TARGETS.has(target)) throw new Error("Formato de destino no disponible en la demo.");
      return { content, target_format: target, source_format: "auto", account_digits: target === "a3" ? 8 : 0 };
    },
    view(d) {
      return { format: d.format, filename: d.filename, summary: d.summary || {}, issues: (d.issues || []).slice(0, 10),
               warnings: (d.warnings || []).slice(0, 10), content: String(d.content || "").slice(0, 8000) };
    },
  },
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" },
  });
}

// Respuesta JSON-RPC de tools/call -> { ok, data, error }.
export function unwrap(text) {
  let msg;
  try { msg = JSON.parse(text); } catch (e) { return { ok: false, error: "Respuesta no válida del servidor." }; }
  if (msg.error) return { ok: false, error: String(msg.error.message || "Error del servidor.") };
  const r = msg.result || {};
  let d = r.structuredContent;
  if (d && typeof d === "object" && Object.keys(d).length === 1 && "result" in d) d = d.result;
  if (r.isError) {
    const t = (r.content || []).map((c) => c.text || "").join(" ").trim();
    return { ok: false, error: (t || "No se pudo procesar.").slice(0, 400) };
  }
  if (!d) {
    try { d = JSON.parse((r.content || [])[0].text); } catch (e) { return { ok: false, error: "Respuesta sin datos." }; }
  }
  return { ok: true, data: d };
}

/**
 * @param callTool (slug, name, args, license) => Promise<string> cuerpo JSON-RPC de la respuesta.
 */
export async function demo(request, env, url, slug, callTool) {
  const spec = DEMOS[slug];
  if (!spec) return json({ ok: false, error: "No hay demo para este servidor." }, 404);
  const origin = request.headers.get("origin");
  if (origin && origin !== url.origin) return json({ ok: false }, 403);
  if (!env.HUB_DEMO_LICENSE || !env.USAGE_DB) return json({ ok: false, unavailable: true, error: "La demo no está activa ahora mismo." }, 503);

  let input = {};
  try { input = await request.json(); } catch (e) { return json({ ok: false, error: "Petición no válida." }, 400); }
  let args;
  try { args = spec.args(input || {}); } catch (e) { return json({ ok: false, error: e.message }, 400); }

  const db = env.USAGE_DB, day = today(), ipKey = await hash(clientIp(request), env.LIMITS_SALT || "kf-hub");
  const perIp = num(env.DEMO_PER_IP_DAY, 5);
  if (!(await take(db, "demo_ip", ipKey, day, perIp)))
    return json({ ok: false, limit: true, error: `Has usado las ${perIp} demos de hoy. Consigue tu licencia gratis para seguir.` }, 429);
  if (!(await take(db, "demo_all", "all", day, num(env.DEMO_DAILY_CAP, 300)))) {
    await giveBack(db, "demo_ip", ipKey, day);
    return json({ ok: false, limit: true, error: "Las demos de hoy se han agotado. Consigue tu licencia gratis para seguir." }, 429);
  }

  let out;
  try {
    out = unwrap(await callTool(slug, spec.tool, args, env.HUB_DEMO_LICENSE));
  } catch (e) {
    out = { ok: false, error: "El servidor no responde ahora mismo. Inténtalo en un minuto." };
  }
  if (!out.ok) {
    await giveBack(db, "demo_ip", ipKey, day);
    await giveBack(db, "demo_all", "all", day);
    return json({ ok: false, error: out.error }, 422);
  }
  return json({ ok: true, tool: spec.tool, result: spec.view(out.data) });
}
