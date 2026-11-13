// Informe semanal automático (lunes 07:00 UTC por cron): visitas propias, uso de herramientas y altas de prueba.
// Solo datos agregados que ya guarda el hub (sin correos ni IP). Se envía a REPORT_EMAIL por Resend si existe;
// GET /api/admin/semanal (x-admin-key) devuelve el mismo informe en JSON; con ?enviar=1 además lo envía.
import { today } from "./limits.js";
import { sameKey } from "./visits.js";

export const WEEKLY_CRON = "0 7 * * 1";
const KV_KEY = "weekly:last";

// Umbrales del plan de rescate (docs/plan-rescate.md): qué número cambia la decisión de la semana.
export const GOALS = { visitas: 150, pruebas: 3, licencias_activas: 1 };

async function visitsBlock(db, from, to) {
  const tot = await db.prepare(
    "SELECT COALESCE(SUM(n),0) AS vistas, COALESCE(SUM(entry*n),0) AS visitas FROM visits WHERE day >= ?1 AND day < ?2 AND path NOT LIKE '/ev/%'",
  ).bind(from, to).first();
  const top = async (col, limit = 5) => (await db.prepare(
    `SELECT ${col} AS k, SUM(entry*n) AS visitas, SUM(n) AS vistas FROM visits WHERE day >= ?1 AND day < ?2 AND ${col} != '' AND path NOT LIKE '/ev/%' GROUP BY ${col} ORDER BY visitas DESC, vistas DESC LIMIT ${limit}`,
  ).bind(from, to).all()).results;
  const embudo = (await db.prepare(
    "SELECT substr(path, 5) AS k, SUM(n) AS n FROM visits WHERE day >= ?1 AND day < ?2 AND path LIKE '/ev/%' GROUP BY path ORDER BY n DESC LIMIT 12",
  ).bind(from, to).all()).results;
  return { ...tot, origenes: await top("ref"), campanas: await top("camp"), paginas: await top("path", 8), embudo };
}

async function usageBlock(db, fromTs, toTs) {
  return db.prepare(
    "SELECT COUNT(*) AS llamadas, COALESCE(SUM(ok),0) AS ok, COALESCE(SUM(credits),0) AS creditos, COUNT(DISTINCT lic) AS licencias_activas FROM usage WHERE ts >= ?1 AND ts < ?2",
  ).bind(fromTs, toTs).first();
}

export async function buildWeekly(env, now = Date.now()) {
  const db = env.USAGE_DB;
  if (!db) return null;
  const d = today(now), from = d - 7, prev = d - 14;
  const s = (day) => day * 86_400;
  let visitas = null, visitasPrev = null;
  try { visitas = await visitsBlock(db, from, d); visitasPrev = await visitsBlock(db, prev, from); } catch { /* sin migración 0003 */ }
  const uso = await usageBlock(db, s(from), s(d));
  const usoPrev = await usageBlock(db, s(prev), s(from));
  const pruebasTotal = (await db.prepare("SELECT COUNT(*) AS n FROM hub_limits WHERE kind = 'trial_email' AND day = 0").first())?.n ?? 0;
  let last = null;
  try { last = JSON.parse((await env.OAUTH_KV?.get(KV_KEY)) || "null"); } catch { last = null; }
  const pruebas = last && Number.isFinite(last.pruebasTotal) ? pruebasTotal - last.pruebasTotal : null;
  const r = {
    semana: { desde: new Date(from * 86_400_000).toISOString().slice(0, 10), hasta: new Date((d - 1) * 86_400_000).toISOString().slice(0, 10) },
    visitas, visitasPrev, uso, usoPrev, pruebasTotal, pruebas,
  };
  r.semaforo = {
    visitas: visitas ? visitas.visitas >= GOALS.visitas : null,
    pruebas: pruebas === null ? null : pruebas >= GOALS.pruebas,
    licencias_activas: uso.licencias_activas >= GOALS.licencias_activas,
  };
  return r;
}

const delta = (a, b) => { const x = Number(a || 0) - Number(b || 0); return x === 0 ? "=" : (x > 0 ? `+${x}` : String(x)); };
const mark = (v) => (v === null ? "·" : v ? "OK" : "BAJO");
const list = (rows) => (rows && rows.length ? rows.map((x) => `  - ${x.k}: ${x.visitas} visitas (${x.vistas} vistas)`).join("\n") : "  - (nada)");

export function weeklyText(r) {
  const v = r.visitas, vp = r.visitasPrev || {};
  return [
    `Informe semanal Flint · ${r.semana.desde} a ${r.semana.hasta}`,
    "",
    `[${mark(r.semaforo.visitas)}] Visitas: ${v ? v.visitas : "sin registro"} (${delta(v?.visitas, vp.visitas)} vs semana anterior), ${v ? v.vistas : 0} páginas vistas. Meta ${GOALS.visitas}.`,
    `[${mark(r.semaforo.pruebas)}] Pruebas gratis nuevas: ${r.pruebas === null ? "primera semana (sin base)" : r.pruebas}. Total histórico: ${r.pruebasTotal}. Meta ${GOALS.pruebas}.`,
    `[${mark(r.semaforo.licencias_activas)}] Licencias que usaron herramientas: ${r.uso.licencias_activas} (${delta(r.uso.licencias_activas, r.usoPrev.licencias_activas)}). Llamadas: ${r.uso.llamadas}, correctas ${r.uso.ok}, créditos ${r.uso.creditos}.`,
    "",
    "Origen de las visitas:", list(v?.origenes),
    "Campañas (utm_campaign):", list(v?.campanas),
    "Páginas de entrada:", list(v?.paginas),
    "Embudo (pasos completados):", v?.embudo?.length ? v.embudo.map((x) => `  - ${x.k}: ${x.n}`).join("\n") : "  - (nada)",
    "",
    "Qué hacer: si visitas OK y pruebas BAJO, el problema es la página (copy/CTA); si visitas BAJO, el problema es el canal.",
    "Ingresos y altas al boletín: panel de Stripe y Resend (no los ve el Worker).",
  ].join("\n");
}

export async function sendWeekly(env, r) {
  const to = String(env.REPORT_EMAIL || "").trim();
  const key = String(env.RESEND_API_KEY || "").trim();
  if (!to || !key || !r) return false;
  const from = String(env.EMAIL_FROM || "Flint by KeyFlint <licenses@keyflint.dev>").trim();
  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { authorization: `Bearer ${key}`, "content-type": "application/json", "user-agent": "mcp-hub-weekly" },
      body: JSON.stringify({ from, to: [to], subject: `Flint semanal ${r.semana.hasta}: ${r.visitas?.visitas ?? 0} visitas, ${r.pruebas ?? "?"} pruebas`, text: weeklyText(r) }),
      signal: AbortSignal.timeout(8000),
    });
    return res.ok;
  } catch (e) { console.error("weekly resend", e?.message); return false; }
}

export async function weekly(env, now = Date.now()) {
  const r = await buildWeekly(env, now);
  if (!r) return null;
  const sent = await sendWeekly(env, r);
  await env.OAUTH_KV?.put(KV_KEY, JSON.stringify({ pruebasTotal: r.pruebasTotal, at: now }));
  return { ...r, enviado: sent };
}

export async function weeklyReport(request, env, url) {
  const headers = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
  const want = env.HUB_ADMIN_KEY || env.KEYFLINT_ADMIN_KEY || "";
  if (!sameKey(request.headers.get("x-admin-key") || "", want)) return new Response('{"ok":false}', { status: 403, headers });
  const r = url.searchParams.get("enviar") === "1" ? await weekly(env) : await buildWeekly(env);
  return new Response(JSON.stringify({ ok: !!r, ...r, texto: r ? weeklyText(r) : "" }), { headers });
}
