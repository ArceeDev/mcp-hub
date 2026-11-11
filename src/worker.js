// API mínima de mcp.keyflint.dev. Solo responde en /api/*; el resto lo sirven los assets estáticos.
// Hace de puente con el gateway de KeyFlint para que el navegador no necesite CORS
// y para devolver solo los campos imprescindibles (la licencia solo en /api/licencia, a quien trae el cs_ del pago).

import { clientIp, giveBack, hash, num, take, today } from "./limits.js";
import { confirmNewsletter, startNewsletter, unsubscribeNewsletter } from "./newsletter.js";

const LICENSE_RE = /^[A-Za-z0-9._~+\/=-]{6,1024}$/;
const SESSION_RE = /^cs_[A-Za-z0-9_]{10,250}$/;
const EMAIL_RE = /^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$/;

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
      "referrer-policy": "no-referrer",
    },
  });
}

function sameOrigin(request, url) {
  const origin = request.headers.get("origin");
  return !origin || origin === url.origin;
}

async function gateway(env, path, init) {
  const base = (env.GATEWAY_URL || "https://licenses.keyflint.dev").replace(/\/$/, "");
  const res = await fetch(base + path, {
    ...init,
    headers: { accept: "application/json", "content-type": "application/json", "user-agent": "mcp-hub-worker", ...(init.headers || {}) },
    signal: AbortSignal.timeout(10000),
  });
  let data = null;
  try { data = await res.json(); } catch (e) { /* respuesta no JSON */ }
  return { ok: res.ok, status: res.status, data };
}

async function balance(request, env, url) {
  const license = (url.searchParams.get("license") || "").trim(), L = (es, e) => (url.searchParams.get("lang") === "en" ? e : es);
  if (!LICENSE_RE.test(license)) return json({ ok: false, error: L("Licencia con formato no válido.", "Invalid license format.") }, 400);
  try {
    const r = await gateway(env, "/api/v1/billing/status?license_key=" + encodeURIComponent(license), { method: "GET" });
    if (r.status === 404 || r.status === 401 || r.status === 403 || r.status === 422)
      return json({ ok: false, error: "No encontramos esa licencia. Revisa que esté completa." }, 404);
    if (!r.ok || !r.data || !r.data.data) return json({ ok: false, error: "KeyFlint no responde ahora mismo. Inténtalo en un minuto." }, 502);
    const d = r.data.data;
    return json({
      ok: true,
      tier: String(d.tier || ""),
      status: String(d.status || ""),
      balance: Number(d.credit_balance) || 0,
      allowance: Number(d.total_allowance) || 0,
      consumed: Number(d.consumed) || 0,
    });
  } catch (e) {
    return json({ ok: false, error: L("KeyFlint no responde ahora mismo. Inténtalo en un minuto.", "KeyFlint is not responding right now. Please try again in a minute.") }, 502);
  }
}

async function reveal(request, env, url) {
  const sid = (url.searchParams.get("session_id") || "").trim();
  if (!SESSION_RE.test(sid)) return json({ ok: false, error: "Enlace de pago no válido." }, 400);
  try {
    const r = await gateway(env, "/api/v1/billing/checkout/" + encodeURIComponent(sid) + "/license", { method: "GET" });
    const code = r.data && r.data.error && r.data.error.code;
    if (r.status === 404) return json({ ok: false, pending: true, error: "Aún estamos emitiendo tu licencia." }, 404);
    if (r.status === 410) return json({ ok: false, error: code === "LICENSE_INACTIVE"
      ? "Esta licencia ya no está activa." : "Este enlace ha caducado. Usa el correo o pide un enlace abajo." }, 410);
    if (!r.ok || !r.data || !r.data.data) return json({ ok: false, error: "KeyFlint no responde ahora mismo. Te llega por correo." }, 502);
    const d = r.data.data;
    return json({ ok: true, license: String(d.license_key || ""), tier: String(d.tier || ""),
      email_hint: d.email_hint ? String(d.email_hint) : null });
  } catch (e) {
    return json({ ok: false, error: "KeyFlint no responde ahora mismo. Te llega por correo." }, 502);
  }
}

async function recover(request, env, url) {
  if (!sameOrigin(request, url)) return json({ ok: false }, 403);
  let email = "", en = false, newsletter = false, L = (es, e) => (en ? e : es);
  try {
    const b = await request.json();
    email = String(b.email || "").trim();
    en = b.lang === "en";
    newsletter = b.newsletter === true;
  } catch (e) { /* cuerpo no válido */ }
  if (!EMAIL_RE.test(email)) return json({ ok: false, error: "Escribe un correo válido." }, 400);
  try {
    await gateway(env, "/api/v1/billing/portal/lookup", { method: "POST", body: JSON.stringify({ query: email }) });
  } catch (e) {
    return json({ ok: false, error: L("KeyFlint no responde ahora mismo. Inténtalo en un minuto.", "KeyFlint is not responding right now. Please try again in a minute.") }, 502);
  }
  // Misma respuesta exista o no el correo: no revela quién es cliente.
  return json({ ok: true });
}

// Prueba gratis: licencia Community (25 créditos) en pantalla. Una por correo (para siempre) y TRIAL_PER_IP_DAY por IP y día.
// Con KEYFLINT_ADMIN_KEY la emite el Worker (POST /api/v1/licenses/issue) y la devuelve; sin ella, KeyFlint la envía por correo.
async function trial(request, env, url) {
  if (!sameOrigin(request, url)) return json({ ok: false }, 403);
  const ip = clientIp(request);
  if (env.TRIAL_LIMIT) {
    const { success } = await env.TRIAL_LIMIT.limit({ key: "trial:" + ip });
    if (!success) return json({ ok: false, error: "Demasiados intentos. Espera un minuto." }, 429);
  }
  let email = "", en = false, newsletter = false, L = (es, e) => (en ? e : es);
  try {
    const b = await request.json();
    email = String(b.email || "").trim();
    en = b.lang === "en";
    newsletter = b.newsletter === true;
  } catch (e) { /* cuerpo no válido */ }
  if (!EMAIL_RE.test(email) || email.length > 254) return json({ ok: false, error: "Escribe un correo válido." }, 400);
  const db = env.USAGE_DB;
  if (!db) return json({ ok: false, unavailable: true, error: "La prueba gratis no está activa ahora mismo." }, 503);

  const salt = env.LIMITS_SALT || "kf-hub";
  const day = today(), ipKey = await hash(ip, salt), mailKey = await hash(email, salt);
  if (!(await take(db, "trial_ip", ipKey, day, num(env.TRIAL_PER_IP_DAY, 2))))
    return json({ ok: false, error: "Ya se han pedido varias licencias de prueba desde tu conexión hoy. Vuelve mañana." }, 429);
  if (!(await take(db, "trial_email", mailKey, 0, 1))) {
    await giveBack(db, "trial_ip", ipKey, day);
    return json({ ok: false, used: true, error: "Ese correo ya tiene su licencia de prueba. Si la perdiste, recupérala por correo." }, 409);
  }
  const undo = async () => { await giveBack(db, "trial_email", mailKey, 0); await giveBack(db, "trial_ip", ipKey, day); };

  try {
    if (env.KEYFLINT_ADMIN_KEY) {
      const r = await gateway(env, "/api/v1/licenses/issue", {
        method: "POST",
        headers: { "x-admin-key": env.KEYFLINT_ADMIN_KEY },
        body: JSON.stringify({ customer_email: email, tier: "community", metadata: { trial: true, source: "mcp-hub", lang: en ? "en" : "es" } }),
      });
      const d = r.data && r.data.data;
      if (!r.ok || !d || !LICENSE_RE.test(String(d.license_key || ""))) {
        await undo();
        console.error("trial issue failed", r.status);
        return json({ ok: false, error: L("KeyFlint no responde ahora mismo. Inténtalo en un minuto.", "KeyFlint is not responding right now. Please try again in a minute.") }, 502);
      }
      let extra = {};
      if (newsletter && env.RESEND_API_KEY && env.OAUTH_KV) {
        const nr = await startNewsletter(env, request, email, "probar").catch(() => null);
        if (nr?.ok && !nr.already) extra = { newsletter_sent: true };
      }
      return json({ ok: true, license: String(d.license_key), tier: "community", credits: 25, ...extra });
    }
    const r = await gateway(env, "/api/v1/billing/trial", { method: "POST", body: JSON.stringify({ email, source: "mcp-hub" }) });
    if (r.status === 503) { await undo(); return json({ ok: false, unavailable: true, error: "La prueba gratis no está activa ahora mismo." }, 503); }
    if (!r.ok) { await undo(); return json({ ok: false, error: "KeyFlint no responde ahora mismo. Inténtalo en un minuto." }, 502); }
    let extra = {};
    if (newsletter && env.RESEND_API_KEY && env.OAUTH_KV) {
      const nr = await startNewsletter(env, request, email, "probar").catch(() => null);
      if (nr?.ok && !nr.already) extra = { newsletter_sent: true };
    }
    return json({ ok: true, emailed: true, ...extra });
  } catch (e) {
    await undo();
    return json({ ok: false, error: L("KeyFlint no responde ahora mismo. Inténtalo en un minuto.", "KeyFlint is not responding right now. Please try again in a minute.") }, 502);
  }
}

// Recarga libre: el gateway crea la sesión de Stripe y suma los créditos a ESTA licencia al cobrar.
// Aquí solo validamos, limitamos por IP y no dejamos que el navegador elija los créditos.
const TOPUP_MIN = 5, TOPUP_MAX = 500;
const RETURN_PATH_RE = /^\/(?:[a-z0-9-]{1,48}\/){1,2}$/;
const TOPUP_ERRORS_EN = { 400: "Choose a whole euro amount between €5 and €500.", 404: "We could not find that license. Check that you pasted the full key.", 409: "This license is not active. Email us at support@keyflint.dev.", 429: "You have reached today's top-up limit for this license. Try tomorrow or email us.", 503: "Top-ups are not available right now. Please try again later." };
const TOPUP_ERRORS = {
  400: "Elige un importe entre 5 € y 500 €, sin decimales.",
  404: "No encontramos esa licencia. Revisa que esté completa.",
  409: "Esta licencia no está activa. Escríbenos a support@keyflint.dev.",
  429: "Has llegado al límite de recargas de hoy para esta licencia. Vuelve mañana o escríbenos.",
  503: "Las recargas no están disponibles ahora mismo. Inténtalo más tarde.",
};

async function topup(request, env, url) {
  if (!sameOrigin(request, url)) return json({ ok: false }, 403);
  let body = {};
  try { body = await request.json(); } catch (e) { /* cuerpo no válido */ }
  const license = String(body.license || "").trim();
  const amount = body.amount;
  const currency = String(body.currency || "eur").toLowerCase(), en = body.lang === "en", errs = en ? TOPUP_ERRORS_EN : TOPUP_ERRORS, L = (es, e) => (en ? e : es);
  if (!LICENSE_RE.test(license)) return json({ ok: false, error: L("Licencia con formato no válido.", "Invalid license format.") }, 400);
  if (!Number.isInteger(amount) || amount < TOPUP_MIN || amount > TOPUP_MAX) return json({ ok: false, error: errs[400] }, 400);
  if (currency !== "eur" && currency !== "usd") return json({ ok: false, error: L("Moneda no admitida.", "Unsupported currency.") }, 400);
  if (body.waiver !== true) return json({ ok: false, error: L("Marca la casilla para recibir los créditos ya.", "Tick the box to receive the credits immediately.") }, 400);
  const db = env.USAGE_DB, ip = clientIp(request), day = today();
  let ipKey = null;
  if (db) {
    ipKey = await hash(ip, env.LIMITS_SALT || "kf-hub");
    if (!(await take(db, "topup_ip", ipKey, day, num(env.TOPUP_PER_IP_DAY, 10))))
      return json({ ok: false, error: L("Demasiados intentos de pago desde tu conexión. Inténtalo mañana.", "Too many payment attempts from your connection. Try again tomorrow.") }, 429);
  }
  // Vuelta a la página donde estaba convirtiendo (p. ej. /lote/): solo rutas propias, el origen lo fija el Worker.
  const rp = typeof body.return_path === "string" && RETURN_PATH_RE.test(body.return_path) ? body.return_path : (en ? "/en/balance/" : "/saldo/");
  const back = (env.PUBLIC_URL || "https://mcp.keyflint.dev").replace(/\/$/, "") + rp;
  try {
    const r = await gateway(env, "/api/v1/billing/topup", {
      method: "POST",
      body: JSON.stringify({ license_key: license, amount_cents: amount * 100, currency, return_url: back }),
    });
    const d = r.data && r.data.data;
    if (r.ok && d && typeof d.checkout_url === "string" && /^https:\/\//.test(d.checkout_url))
      return json({ ok: true, url: d.checkout_url, credits: Number(d.credits) || 0 });
    if (db && ipKey) await giveBack(db, "topup_ip", ipKey, day);
    const st = r.status === 422 ? 400 : r.status;
    return json({ ok: false, error: errs[st] || L("KeyFlint no responde ahora mismo. Inténtalo en un minuto.", "KeyFlint is not responding right now. Please try again in a minute.") }, errs[st] ? st : 502);
  } catch (e) {
    if (db && ipKey) await giveBack(db, "topup_ip", ipKey, day);
    return json({ ok: false, error: L("KeyFlint no responde ahora mismo. Inténtalo en un minuto.", "KeyFlint is not responding right now. Please try again in a minute.") }, 502);
  }
}

async function topupStatus(request, env, url) {
  const sid = (url.searchParams.get("session") || "").trim();
  if (!SESSION_RE.test(sid)) return json({ ok: false, error: "Enlace de pago no válido." }, 400);
  try {
    const r = await gateway(env, "/api/v1/billing/topup/" + encodeURIComponent(sid), { method: "GET" });
    const d = r.data && r.data.data;
    if (!r.ok || !d) return json({ ok: false, error: "KeyFlint no responde ahora mismo." }, 502);
    return json({ ok: true, status: String(d.status || "pending"), credits: Number(d.credits) || 0,
      balance: Number(d.credit_balance) || 0 });
  } catch (e) {
    return json({ ok: false, error: "KeyFlint no responde ahora mismo." }, 502);
  }
}

async function newsletterStart(request, env, url) {
  if (!sameOrigin(request, url)) return json({ ok: false }, 403);
  let body = {};
  try { body = await request.json(); } catch (e) { /* json inválido */ }
  const r = await startNewsletter(env, request, body.email, body.source);
  if (!r.ok) return json({ ok: false, error: r.error }, r.status || 400);
  return json({ ok: true, ...(r.already ? { already: true } : {}) });
}

async function newsletterConfirm(request, env, url) {
  if (!sameOrigin(request, url)) return json({ ok: false }, 403);
  let body = {};
  try { body = await request.json(); } catch (e) { /* json inválido */ }
  const r = await confirmNewsletter(env, body.token);
  if (!r.ok) return json({ ok: false, error: r.error }, r.status || 400);
  return json({ ok: true });
}

async function newsletterUnsub(request, env, url) {
  if (!sameOrigin(request, url)) return json({ ok: false }, 403);
  let body = {};
  try { body = await request.json(); } catch (e) { /* json inválido */ }
  const r = await unsubscribeNewsletter(env, body.token);
  if (!r.ok) return json({ ok: false, error: r.error }, r.status || 400);
  return json({ ok: true, ...(r.already ? { already: true } : {}) });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/saldo" && request.method === "GET") return balance(request, env, url);
    if (url.pathname === "/api/licencia" && request.method === "GET") return reveal(request, env, url);
    if (url.pathname === "/api/recuperar" && request.method === "POST") return recover(request, env, url);
    if (url.pathname === "/api/prueba" && request.method === "POST") return trial(request, env, url);
    if (url.pathname === "/api/recarga" && request.method === "POST") return topup(request, env, url);
    if (url.pathname === "/api/recarga" && request.method === "GET") return topupStatus(request, env, url);
    if (url.pathname === "/api/boletin/alta" && request.method === "POST") return newsletterStart(request, env, url);
    if (url.pathname === "/api/boletin/confirmar" && request.method === "POST") return newsletterConfirm(request, env, url);
    if (url.pathname === "/api/boletin/baja" && request.method === "POST") return newsletterUnsub(request, env, url);
    if (url.pathname.startsWith("/api/")) return json({ ok: false, error: "No encontrado." }, 404);
    return env.ASSETS.fetch(request);
  },
};
