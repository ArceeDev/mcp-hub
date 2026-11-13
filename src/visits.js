// Registro propio de visitas, agregado y sin datos personales (RGPD/LSSI art. 22.2: sin cookies ni almacenamiento en el equipo).
// POST /api/v  -> suma 1 a la fila del día. Las rutas /ev/<paso> son pasos del embudo (licencia, conversión, descarga...). GET /api/admin/visitas?dias=N (x-admin-key) -> resumen.
import { clientIp, hash, num, take, today } from "./limits.js";

const BOT_RE = /bot|crawl|spider|slurp|preview|headless|lighthouse|monitor|curl|wget|python|httpclient|scrapy/i;
const TOKEN_RE = /^[a-z0-9._-]{1,40}$/;
const PATH_RE = /^\/[a-z0-9\-\/]{0,119}$/;
const MAX_PER_IP_DAY = 300; // freno anti-inflado; la IP solo existe como hash en hub_limits y se purga con el día

const tok = (v) => { const s = String(v || "").trim().toLowerCase(); return TOKEN_RE.test(s) ? s : ""; };

export function refHost(raw, ownHost) {
  try {
    const h = new URL(String(raw)).hostname.toLowerCase().replace(/^www\./, "");
    return !h || h === ownHost || h.length > 80 ? "" : h;
  } catch { return ""; }
}

export async function recordVisit(request, env, url) {
  const noContent = () => new Response(null, { status: 204, headers: { "cache-control": "no-store" } });
  const origin = request.headers.get("origin");
  if (origin && origin !== url.origin) return noContent();
  const ua = request.headers.get("user-agent") || "";
  if (!ua || BOT_RE.test(ua)) return noContent();
  const dev = /Mobi|Android|iPhone|iPad/i.test(ua) ? "m" : "d";
  const asn = Number.isInteger(request.cf?.asn) ? request.cf.asn : 0;
  const db = env.USAGE_DB;
  if (!db) return noContent();
  let b;
  try { b = JSON.parse((await request.text()).slice(0, 2048)); } catch { return noContent(); }
  const p = String(b.p || "/").toLowerCase();
  const path = PATH_RE.test(p) ? p : "/otros";
  const ref = refHost(b.r, url.hostname.replace(/^www\./, ""));
  const country = /^[A-Z]{2}$/.test(request.cf?.country || "") ? request.cf.country : "XX";
  const day = today();
  if (!(await take(db, "visit_ip", await hash(clientIp(request), "v" + day), day, MAX_PER_IP_DAY))) return noContent();
  await db.prepare(
    "INSERT INTO visits (day, path, ref, src, med, camp, country, entry, dev, asn, n) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, 1) " +
    "ON CONFLICT (day, path, ref, src, med, camp, country, entry, dev, asn) DO UPDATE SET n = n + 1",
  ).bind(day, path, ref, tok(b.s), tok(b.m), tok(b.c), country, b.e ? 1 : 0, dev, asn).run();
  return noContent();
}

export function sameKey(a, b) {
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  if (!x.length || x.length !== y.length) return false;
  let d = 0;
  for (let i = 0; i < x.length; i++) d |= x[i] ^ y[i];
  return d === 0;
}

export async function visitsReport(request, env, url) {
  const want = env.HUB_ADMIN_KEY || env.KEYFLINT_ADMIN_KEY || "";
  const headers = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
  if (!sameKey(request.headers.get("x-admin-key") || "", want)) return new Response('{"ok":false}', { status: 403, headers });
  const from = today() - Math.min(num(url.searchParams.get("dias"), 30), 400) + 1;
  const q = async (col, limit = 25) => (await env.USAGE_DB.prepare(
    `SELECT ${col} AS k, SUM(n) AS vistas, SUM(entry * n) AS visitas FROM visits WHERE day >= ?1 AND path NOT LIKE '/ev/%' GROUP BY ${col} ORDER BY vistas DESC LIMIT ${limit}`,
  ).bind(from).all()).results;
  const total = await env.USAGE_DB.prepare("SELECT COALESCE(SUM(n),0) AS vistas, COALESCE(SUM(entry*n),0) AS visitas FROM visits WHERE day >= ?1 AND path NOT LIKE '/ev/%'").bind(from).first();
  const embudo = (await env.USAGE_DB.prepare(
    "SELECT substr(path, 5) AS k, SUM(n) AS n FROM visits WHERE day >= ?1 AND path LIKE '/ev/%' GROUP BY path ORDER BY n DESC LIMIT 30",
  ).bind(from).all()).results;
  return new Response(JSON.stringify({
    ok: true, desde: new Date(from * 86_400_000).toISOString().slice(0, 10), total,
    por_dia: await q("day", 400), paises: await q("country"), origenes: await q("ref"),
    utm_source: await q("src"), utm_campaign: await q("camp"), paginas: await q("path", 40),
    dispositivos: await q("dev", 5), redes_asn: await q("asn"), embudo,
  }), { headers });
}
