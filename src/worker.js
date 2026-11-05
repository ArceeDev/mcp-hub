// API mínima de mcp.keyflint.dev. Solo responde en /api/*; el resto lo sirven los assets estáticos.
// Hace de puente con el gateway de KeyFlint para que el navegador no necesite CORS
// y para devolver solo los campos imprescindibles (la licencia solo en /api/licencia, a quien trae el cs_ del pago).

const LICENSE_RE = /^[A-Za-z0-9._~+\/=-]{6,400}$/;
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
    headers: { accept: "application/json", "content-type": "application/json", "user-agent": "mcp-hub-worker" },
    signal: AbortSignal.timeout(10000),
  });
  let data = null;
  try { data = await res.json(); } catch (e) { /* respuesta no JSON */ }
  return { ok: res.ok, status: res.status, data };
}

async function balance(request, env, url) {
  const license = (url.searchParams.get("license") || "").trim();
  if (!LICENSE_RE.test(license)) return json({ ok: false, error: "Licencia con formato no válido." }, 400);
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
    return json({ ok: false, error: "KeyFlint no responde ahora mismo. Inténtalo en un minuto." }, 502);
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
  let email = "";
  try { email = String((await request.json()).email || "").trim(); } catch (e) { /* cuerpo no válido */ }
  if (!EMAIL_RE.test(email)) return json({ ok: false, error: "Escribe un correo válido." }, 400);
  try {
    await gateway(env, "/api/v1/billing/portal/lookup", { method: "POST", body: JSON.stringify({ query: email }) });
  } catch (e) {
    return json({ ok: false, error: "KeyFlint no responde ahora mismo. Inténtalo en un minuto." }, 502);
  }
  // Misma respuesta exista o no el correo: no revela quién es cliente.
  return json({ ok: true });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/saldo" && request.method === "GET") return balance(request, env, url);
    if (url.pathname === "/api/licencia" && request.method === "GET") return reveal(request, env, url);
    if (url.pathname === "/api/recuperar" && request.method === "POST") return recover(request, env, url);
    if (url.pathname.startsWith("/api/")) return json({ ok: false, error: "No encontrado." }, 404);
    return env.ASSETS.fetch(request);
  },
};
