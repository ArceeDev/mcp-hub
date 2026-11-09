// mcp.keyflint.dev: web estática, API mínima (/api/*) y los MCP remotos con OAuth.
//
//   https://mcp.keyflint.dev/despacho/mcp conector único para asesorías: Norma 43 + ContaBridge con una URL
//   https://mcp.keyflint.dev/<slug>/mcp   MCP remoto (Streamable HTTP). Claude, ChatGPT, Antigravity, Codex… lo añaden
//                                          por URL; el cliente hace OAuth y el usuario pega su licencia una vez.
//   /authorize                            página de licencia (consentimiento OAuth)
//   /oauth/token, /oauth/register, /.well-known/…   servidor de autorización (OAuth 2.1 + DCR + CIMD)
//
// El token OAuth guarda la licencia cifrada en sus props (KV OAUTH_KV). Cada petición MCP llega al contenedor con la
// licencia en X-License-Key y sin el token: el servidor Python cobra créditos con ella. Los clientes que admiten
// cabeceras pueden saltarse OAuth y mandar `Authorization: Bearer LIC-…` directamente.

import { Container, getRandom } from "@cloudflare/containers";
import {
  AuthorizationError,
  CimdFetchError,
  OAuthAuthorizationServer,
  OAuthResourceServer,
} from "@cloudflare/workers-oauth-provider";
import api from "./worker.js";
import { EMAIL_RE, bindLicense, closeSession, issueTrial, licensesFor, normEmail, openSession, readSession, startEmailLogin, verifyEmailCode } from "./emailauth.js";
import { demo } from "./demo.js";
import { status } from "./status.js";

import { NAMES, SLUGS } from "./slugs.js";

export { SLUGS };
const SCOPE = "mcp";
const LICENSE_RE = /^LIC-[A-Za-z0-9._~+\/=-]{6,1024}$/;
const INSTANCES = 1; // 1 contenedor primario caliente evita 3x cold-starts; escalable con MCP_INSTANCES
const QUIET = new Set(["credits_balance", "pricing"]); // gratis y frecuentes: no ensucian el historial

export class McpRuntime extends Container {
  defaultPort = 8080;
  sleepAfter = "10m";
  enableInternet = true; // Web Intel lee webs; todos cobran contra licenses.keyflint.dev

  async fetch(request) {
    if (request.headers.get("x-container-restart") === "1") {
      try {
        await this.destroy();
      } catch (e) {
        console.error("container destroy error", e?.message);
      }
      return new Response("restarted", { status: 200 });
    }
    return super.fetch(request);
  }
}

const origin = (env) => (env.PUBLIC_ORIGIN || "https://mcp.keyflint.dev").replace(/\/$/, "");

let cached = null;
function servers(env) {
  const base = origin(env);
  if (cached && cached.base === base) return cached;
  const as = new OAuthAuthorizationServer({
    issuer: base,
    resources: SLUGS.map((s) => `${base}/${s}/mcp`),
    scopesSupported: [SCOPE, "offline_access"],
    clientRegistrationEndpoint: "/oauth/register",
    clientIdMetadataDocumentEnabled: true,
    accessTokenTTL: 3600,
    refreshTokenTTL: 90 * 86400,
    refreshTokenIdleTTL: 30 * 86400,
  });
  const resources = Object.fromEntries(SLUGS.map((slug) => [slug, new OAuthResourceServer({
    resourceMetadata: { resource: `${base}/${slug}/mcp`, authorization_servers: [base], resource_name: NAMES[slug] },
    requiredScopes: [SCOPE],
    validateToken: (env) => async (resource, token) => {
      // Licencia directa en la cabecera (Cursor, VS Code, Codex, Claude Code…): sin OAuth.
      if (LICENSE_RE.test(token)) return { props: { license: token }, audience: resource, scope: [SCOPE] };
      return as.validateToken(resource, token, env);
    },
    handler: { fetch: (request, env, ctx) => forward(request, env, ctx, ctx.props && ctx.props.license) },
  })]));
  cached = { base, as, resources };
  return cached;
}

async function forward(request, env, ctx, license) {
  if (!license || !LICENSE_RE.test(license)) return new Response("Licencia no válida", { status: 401 });
  const url = new URL(request.url);
  const slug = url.pathname.split("/")[1];
  const who = await userId(license);
  const body = request.method === "POST" ? await request.text() : null;
  const call = toolCall(body);

  // Límite por licencia (frena bucles de agentes y abusos). Solo cuenta llamadas a herramientas.
  if (call && env.MCP_LIMIT) {
    const { success } = await env.MCP_LIMIT.limit({ key: who });
    if (!success) return rpcError(call.id, -32029, "Demasiadas llamadas seguidas con esta licencia. Espera un minuto.", 429);
  }

  const headers = new Headers(request.headers);
  for (const h of ["authorization", "cookie", "x-license-key", "cf-connecting-ip", "x-forwarded-for", "content-length"]) headers.delete(h);
  headers.set("x-license-key", license);
  const upstream = new Request(`http://mcp${url.pathname}${url.search}`, { method: request.method, headers, body, redirect: "manual" });
  const t0 = Date.now();
  const res = await upstreamFetch(env, url, upstream);
  if (!call || !env.USAGE_DB || QUIET.has(call.name)) return res;

  // Registro de uso: MCP, herramienta, resultado, créditos y duración. Nunca la licencia (solo su hash) ni el contenido.
  const text = await res.text();
  const out = parseResult(text);
  ctx.waitUntil(env.USAGE_DB.prepare(
    "INSERT INTO usage (lic, ts, slug, tool, ok, credits, ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
  ).bind(who, Math.floor(t0 / 1000), slug, call.name.slice(0, 64), out.ok ? 1 : 0, out.credits, Date.now() - t0).run()
    .catch((e) => console.error("usage insert", e.message)));
  return new Response(text, { status: res.status, headers: res.headers });
}

async function upstreamFetch(env, url, upstream) {
  // Desarrollo local sin Docker: MCP_UPSTREAM=http://127.0.0.1:8091 (uvicorn container/app.py).
  if (env.MCP_UPSTREAM) return fetch(new Request(env.MCP_UPSTREAM.replace(/\/$/, "") + url.pathname + url.search, upstream));
  const n = Math.max(1, Math.min(5, Number(env.MCP_INSTANCES) || INSTANCES));
  const container = await getRandom(env.MCP_RUNTIME, n);
  return container.fetch(upstream);
}

// Llamada directa de las demos web: JSON-RPC tools/call al contenedor con la licencia interna del hub.
async function demoCall(env, url, slug, name, args, license) {
  const target = new URL(`/${slug}/mcp`, url);
  const upstream = new Request(`http://mcp/${slug}/mcp`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json, text/event-stream", "x-license-key": license },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name, arguments: args } }),
  });
  const res = await upstreamFetch(env, target, upstream);
  return res.text();
}

function toolCall(body) {
  if (!body || body.length > 50_000_000) return null;
  try {
    const m = JSON.parse(body);
    if (m && m.method === "tools/call" && m.params && typeof m.params.name === "string") return { id: m.id ?? null, name: m.params.name };
  } catch (e) { /* no es JSON-RPC */ }
  return null;
}

function parseResult(text) {
  try {
    const r = JSON.parse(text).result;
    if (!r) return { ok: false, credits: 0 };
    let d = r.structuredContent;
    if (d && typeof d === "object" && Object.keys(d).length === 1 && "result" in d) d = d.result;
    const credits = Number(d && d.billing && d.billing.credits_charged) || 0;
    return { ok: !r.isError, credits };
  } catch (e) {
    return { ok: false, credits: 0 };
  }
}

function rpcError(id, code, message, status) {
  return new Response(JSON.stringify({ jsonrpc: "2.0", id, error: { code, message } }), {
    status, headers: { "content-type": "application/json", "retry-after": "60" },
  });
}

// ---------------------------------------------------------------- /api/uso: historial de la licencia

async function usage(request, env, url) {
  const h = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" };
  const license = (url.searchParams.get("license") || "").trim();
  if (!LICENSE_RE.test(license)) return new Response(JSON.stringify({ ok: false, error: "Licencia con formato no válido." }), { status: 400, headers: h });
  if (!env.USAGE_DB) return new Response(JSON.stringify({ ok: true, recent: [], tools: [] }), { headers: h });
  const who = await userId(license);
  const since = Math.floor(Date.now() / 1000) - 30 * 86400;
  const [recent, tools] = await env.USAGE_DB.batch([
    env.USAGE_DB.prepare("SELECT ts, slug, tool, ok, credits, ms FROM usage WHERE lic = ?1 ORDER BY ts DESC LIMIT 10").bind(who),
    env.USAGE_DB.prepare("SELECT slug, tool, COUNT(*) AS calls, SUM(credits) AS credits, SUM(1 - ok) AS errors FROM usage " +
      "WHERE lic = ?1 AND ts >= ?2 GROUP BY slug, tool ORDER BY credits DESC, calls DESC LIMIT 30").bind(who, since),
  ]);
  return new Response(JSON.stringify({ ok: true, recent: recent.results, tools: tools.results }), { headers: h });
}

// ---------------------------------------------------------------- cron diario

async function daily(env) {
  if (env.USAGE_DB) {
    const cutoff = Math.floor(Date.now() / 1000) - 180 * 86400;
    await env.USAGE_DB.prepare("DELETE FROM usage WHERE ts < ?1").bind(cutoff).run();
    // Contadores diarios de prueba gratis y demos: basta con los de los 2 últimos días (day = 0 son permanentes).
    await env.USAGE_DB.prepare("DELETE FROM hub_limits WHERE day > 0 AND day < ?1")
      .bind(Math.floor(Date.now() / 86_400_000) - 2).run();
  }
  if (env.HUB_DEMO_LICENSE && env.KEYFLINT_ADMIN_KEY) {
    const base = (env.GATEWAY_URL || "https://licenses.keyflint.dev").replace(/\/$/, "");
    try {
      const bRes = await fetch(`${base}/api/v1/quota/balance?license_key=${encodeURIComponent(env.HUB_DEMO_LICENSE)}`, {
        headers: { accept: "application/json", "user-agent": "mcp-hub-worker" }, signal: AbortSignal.timeout(8000),
      });
      const bData = await bRes.json().catch(() => ({}));
      const rem = Number(bData?.data?.remaining_credits ?? 9999);
      if (bRes.ok && rem < 500) {
        await fetch(`${base}/api/v1/quota/replenish`, {
          method: "POST",
          headers: { "content-type": "application/json", "x-admin-key": env.KEYFLINT_ADMIN_KEY, "user-agent": "mcp-hub-worker" },
          body: JSON.stringify({ license_key: env.HUB_DEMO_LICENSE, credits: 1000 }),
          signal: AbortSignal.timeout(8000),
        });
      }
    } catch (e) { console.error("demo replenish check", e.message); }
  }
  const res = await upstreamFetch(env, new URL("http://mcp/healthz"), new Request("http://mcp/healthz"));
  const data = await res.json().catch(() => ({}));
  const missing = SLUGS.filter((s) => !(data.servers || []).includes(s));
  if (!res.ok || missing.length) console.error("healthz", res.status, "faltan", missing.join(","));
  else console.log("healthz ok", data.servers.join(","));
}

// ---------------------------------------------------------------- página de licencia (consentimiento)

const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);

function page(title, body, headers = new Headers(), status = 200) {
  headers.set("content-type", "text/html; charset=utf-8");
  headers.set("cache-control", "no-store");
  return new Response(`<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>${esc(title)} · Flint</title><link rel="stylesheet" href="/assets/style.css"><link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" href="/assets/flint-icon.svg">
<style>.auth{max-width:460px;margin:8vh auto;padding:0 16px}.auth .card{background:var(--surface);border:1px solid var(--line);
border-radius:16px;padding:28px}.auth h1{font-size:1.5rem;margin:.2em 0 .5em}.auth input{width:100%;font:inherit;font-family:var(--mono);
font-size:.9rem;padding:.7em .8em;border-radius:10px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--ink)}
.auth .row{display:flex;gap:10px;margin-top:18px}.auth .row .btn{flex:1;justify-content:center}.auth .warn{color:#e5a50a}
.auth .err{color:#ef5350;margin:.6em 0 0}.auth .muted{color:var(--muted);font-size:.9rem}.auth .logo{display:flex;gap:10px;align-items:center;font-weight:600;white-space:nowrap;margin-bottom:12px}
.auth .logo img{width:28px;height:28px}
.auth .lic-opt{border:1px solid var(--line-2);border-radius:10px;padding:12px;margin:8px 0;display:flex;align-items:flex-start;gap:12px;cursor:pointer;background:var(--bg-2);transition:border-color .15s}
.auth .lic-opt:hover{border-color:var(--line)}
.auth .lic-opt input{width:auto;margin-top:3px;cursor:pointer}
.auth details summary{color:var(--muted);cursor:pointer;font-size:.85rem;margin-top:14px}
.auth details summary:hover{color:var(--ink)}</style></head><body><main class="auth"><div class="logo"><img src="/assets/flint-icon.svg" alt="">Flint <span class="muted">by KeyFlint</span></div>
<div class="card">${body}</div></main></body></html>`, { status, headers });
}

function intro(details) {
  const app = esc(details.clientName || "Una aplicación");
  const who = details.clientDomain
    ? `Publicada por <b>${esc(details.clientDomain)}</b>.`
    : "No hemos podido comprobar quién la publica.";
  return `<p>${who} El acceso se enviará a <b>${esc(details.redirectHost)}</b>.</p>
${details.redirectIsLoopback ? '<p class="warn">Esto envía el acceso a una aplicación de tu ordenador. Sigue solo si acabas de iniciar la conexión desde ella.</p>' : ""}`;
}

const err = (e) => (e ? `<p class="err">${esc(e)}</p>` : "");
// El botón principal va primero en el DOM para que Intro conecte (no cancele); order lo pinta a la derecha.
const buttons = (label = "Conectar") => `<div class="row">
  <button class="btn btn-primary" style="order:2" name="decision" value="approve">${label}</button>
  <button class="btn" name="decision" value="deny" formnovalidate>Cancelar</button>
</div>`;

function consentForm(details, handle, error = "", emailPrefill = "") {
  const app = esc(details.clientName || "Una aplicación");
  return `<h1>Conectar ${app}</h1>
${intro(details)}
<p class="muted">Podrá usar los servidores MCP de KeyFlint con tu licencia y gastar sus créditos. Puedes revocarlo cuando quieras.</p>
<form method="post">
<input type="hidden" name="handle" value="${esc(handle)}">
<input type="hidden" name="step" value="start">
<label for="email"><b>Tu correo electrónico</b></label>
<input id="email" name="email" type="email" autocomplete="email" placeholder="nombre@despacho.com" value="${esc(emailPrefill)}">
${err(error)}
<p class="muted" style="margin-top:6px;font-size:.85rem">Te enviaremos un código de 6 dígitos. Si aún no tienes licencia, podrás crear una prueba gratis de 25 créditos.</p>
<details>
  <summary>¿Prefieres introducir tu clave LIC-… directamente?</summary>
  <div style="margin-top:8px"><input id="lic" name="license" autocomplete="off" spellcheck="false" placeholder="LIC-…"></div>
</details>
${buttons("Continuar")}
</form>`;
}

function codeForm(details, handle, email, error = "") {
  return `<h1>Revisa tu correo</h1>
<p>Hemos enviado un código de 6 dígitos a <b>${esc(email)}</b>. Caduca en 10 minutos.</p>
<form method="post">
<input type="hidden" name="handle" value="${esc(handle)}">
<input type="hidden" name="email" value="${esc(email)}">
<label for="code"><b>Código</b></label>
<input id="code" name="code" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9 ]{6,7}" maxlength="7" placeholder="123456" autofocus>
${err(error)}
<input type="hidden" name="step" value="code">
${buttons("Verificar")}
<p class="muted" style="font-size:.85rem">¿No llega? Mira en spam o <button class="btn" style="padding:.2em .6em" name="resend" value="1" formnovalidate>envía otro</button></p>
</form>`;
}

function chooseForm(details, handle, token, email, licenses, error = "") {
  const app = esc(details.clientName || "Una aplicación");
  const opts = licenses.map((lic, i) => {
    const sub = Number.isFinite(lic.credits) ? `${lic.credits} créditos · ${lic.tier || ""}` : (lic.tier || "");
    return `
  <label class="lic-opt"><input type="radio" name="pick" value="${i}" ${i === 0 ? "checked" : ""}>
    <div><b>${esc(lic.name || "Licencia " + (lic.tier || ""))}</b><div class="muted" style="font-size:.8rem">${esc(sub)}</div></div>
  </label>`;
  }).join("");
  const trialOpt = licenses.length ? "" : `<label class="lic-opt"><input type="radio" name="pick" value="trial" checked>
  <div><b>Crear prueba gratis</b><div class="muted" style="font-size:.8rem">25 créditos, una por correo</div></div></label>`;
  return `<h1>${licenses.length ? "Elige tu licencia" : "Conecta una licencia"}</h1>
<p>Correo verificado: <b>${esc(email)}</b>. ${licenses.length ? `Elige con cuál conectar ${app}:` : "Aún no tiene licencias enlazadas."}</p>
<form method="post">
<input type="hidden" name="handle" value="${esc(handle)}">
<input type="hidden" name="vt" value="${esc(token)}">
<input type="hidden" name="step" value="pick">
${opts}
${trialOpt}
<label class="lic-opt"><input type="radio" name="pick" value="lic">
  <div style="flex:1"><b>Usar otra clave LIC-…</b><input name="license" autocomplete="off" spellcheck="false" placeholder="LIC-…" style="margin-top:6px"></div></label>
${err(error)}
${buttons("Conectar")}
</form>`;
}

async function licenseExists(env, license) {
  const base = (env.GATEWAY_URL || "https://licenses.keyflint.dev").replace(/\/$/, "");
  try {
    const r = await fetch(`${base}/api/v1/quota/balance?license_key=${encodeURIComponent(license)}`, {
      headers: { accept: "application/json", "user-agent": "mcp-hub-worker" }, signal: AbortSignal.timeout(8000),
    });
    if (r.ok) return "ok";
    return r.status >= 500 ? "down" : "unknown";
  } catch (e) {
    return "down";
  }
}

async function userId(license) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(license));
  return [...new Uint8Array(d)].slice(0, 12).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function authError(e) {
  if (e instanceof AuthorizationError) {
    if (e.redirectTo) return Response.redirect(e.redirectTo, 302);
    return page("Error", `<h1>No se puede conectar</h1><p>${esc(e.description || e.code)}</p>`, new Headers(), 400);
  }
  if (e instanceof CimdFetchError) {
    return page("Error", "<h1>No se puede conectar</h1><p>No pudimos leer los datos de la aplicación. Vuelve a intentarlo desde ella.</p>", new Headers(), 400);
  }
  throw e;
}

async function authorize(request, env) {
  const oauth = servers(env).as.getOAuthApi(env);
  try {
    if (request.method === "GET") {
      const req = await oauth.parseAuthRequest(request);
      const details = await oauth.describeConsent(req);
      const consent = await oauth.beginConsent(req);
      return page(`Conectar ${details.clientName || ""}`, consentForm(details, consent.handle), consent.headers);
    }
    if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
    const form = await request.formData();
    const handle = String(form.get("handle") || "");
    const resend = form.get("resend") === "1";
    if (form.get("decision") !== "approve" && !resend) {
      const denied = await oauth.denyConsent(request, handle);
      return new Response(null, { status: 302, headers: denied.headers });
    }
    // approveConsent consume el formulario; cada paso que no conecta abre otro con la misma petición validada.
    const approved = await oauth.approveConsent(request, handle, { scope: [SCOPE, "offline_access"] });
    const step = resend ? "resend" : String(form.get("step") || "start");
    const email = normEmail(form.get("email"));
    let license = String(form.get("license") || "").trim();
    const again = async (title, render, status = 200) => {
      const details = await oauth.describeConsent(approved.request);
      const next = await oauth.beginConsent(approved.request);
      return page(title, render(details, next.handle), next.headers, status);
    };
    const back = (msg, status = 400, prefill = email) => again("Conectar", (d, h) => consentForm(d, h, msg, prefill), status);

    let verified = "", token = "";
    if (step === "start" && !license) {
      if (!email) return back("Escribe tu correo o tu clave LIC-….");
      const r = await startEmailLogin(env, request, email);
      if (!r.ok) return back(r.error, r.status);
      return again("Revisa tu correo", (d, h) => codeForm(d, h, email));
    }
    if (step === "resend") {
      const r = await startEmailLogin(env, request, email);
      if (!r.ok) return again("Revisa tu correo", (d, h) => codeForm(d, h, email, r.error), r.status);
      return again("Revisa tu correo", (d, h) => codeForm(d, h, email, "Te hemos enviado un código nuevo."));
    }
    if (step === "code") {
      if (!EMAIL_RE.test(email)) return back("Introduce un correo válido.");
      const r = await verifyEmailCode(env, email, form.get("code"));
      if (!r.ok) {
        if (r.expired) return back(r.error, r.status);
        return again("Revisa tu correo", (d, h) => codeForm(d, h, email, r.error), r.status);
      }
      verified = email;
      const list = await licensesFor(env, email);
      if (list.length === 1 && (await licenseExists(env, list[0].key)) === "ok") license = list[0].key;
      else {
        token = await openSession(env, email);
        return again("Elige tu licencia", (d, h) => chooseForm(d, h, token, email, list));
      }
    }
    if (step === "pick") {
      token = String(form.get("vt") || "");
      verified = await readSession(env, token);
      if (!verified) return back("La verificación ha caducado. Vuelve a pedir el código.", 400, "");
      const list = await licensesFor(env, verified);
      const pick = String(form.get("pick") || "");
      const retry = (msg, status = 400) => again("Elige tu licencia", (d, h) => chooseForm(d, h, token, verified, list, msg), status);
      if (pick === "trial") {
        const r = await issueTrial(env, request, verified);
        if (!r.ok) return retry(r.error, r.status);
        license = r.license;
      } else if (pick === "lic") {
        const state = LICENSE_RE.test(license) ? await licenseExists(env, license) : "format";
        if (state !== "ok") return retry(state === "down" ? "KeyFlint no responde ahora mismo. Inténtalo en un minuto." : "No encontramos esa licencia. Revisa que esté completa.");
        await bindLicense(env, verified, { key: license, tier: "registrada", name: "Licencia " + license.slice(4, 10) + "…" });
      } else if (/^\d{1,2}$/.test(pick) && list[Number(pick)]) {
        license = list[Number(pick)].key;
      } else return retry("Elige una opción.");
      await closeSession(env, token);
    }

    // Camino directo (clave LIC-) o licencia elegida: se comprueba siempre contra KeyFlint antes de conectar.
    const state = LICENSE_RE.test(license) ? await licenseExists(env, license) : "format";
    if (state !== "ok") {
      const msg = state === "format" ? "Eso no parece una licencia. Empieza por LIC- y viene en el correo de compra."
        : state === "down" ? "KeyFlint no responde ahora mismo. Inténtalo en un minuto."
          : "No encontramos esa licencia. Revisa que esté completa.";
      return back(msg, 400, verified || email);
    }
    const { redirectTo } = await oauth.completeAuthorization({
      request: approved.request,
      userId: await userId(license),
      metadata: { email: verified || null, connected: new Date().toISOString() },
      scope: approved.request.scope,
      props: { license, email: verified || null },
    });
    approved.headers.set("location", redirectTo);
    return new Response(null, { status: 302, headers: approved.headers });
  } catch (e) {
    return authError(e);
  }
}

// ---------------------------------------------------------------- enrutado

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const { as, resources } = servers(env);
    if (path === "/authorize") return authorize(request, env);
    if (path === "/api/uso" && request.method === "GET") return usage(request, env, url);
    if (path === "/api/admin/restart" && request.method === "POST") {
      // Sin esto cualquiera podía reiniciar los contenedores (DoS). Clave: HUB_ADMIN_KEY o, si no existe, KEYFLINT_ADMIN_KEY.
      const want = env.HUB_ADMIN_KEY || env.KEYFLINT_ADMIN_KEY || "";
      const got = request.headers.get("x-admin-key") || "";
      if (!want || got.length !== want.length || !crypto.subtle.timingSafeEqual(new TextEncoder().encode(got), new TextEncoder().encode(want)))
        return new Response(JSON.stringify({ ok: false }), { status: 403, headers: { "content-type": "application/json" } });
      const n = Math.max(1, Math.min(5, Number(env.MCP_INSTANCES) || INSTANCES));
      for (let i = 0; i < n; i++) {
        const id = env.MCP_RUNTIME.idFromName(`instance-${i}`);
        const stub = env.MCP_RUNTIME.get(id);
        await stub.fetch(new Request("http://mcp/restart", { headers: { "x-container-restart": "1" } })).catch(() => {});
      }
      return new Response(JSON.stringify({ ok: true, message: "Containers restarted" }), {
        headers: { "content-type": "application/json" },
      });
    }
    if (path === "/api/estado" && request.method === "GET")
      return status(env, ctx, SLUGS, () => upstreamFetch(env, new URL("http://mcp/healthz"), new Request("http://mcp/healthz")));
    const dm = path.match(/^\/api\/demo\/([a-z0-9-]+)$/);
    if (dm && request.method === "POST") return demo(request, env, url, dm[1], (slug, name, args, lic) => demoCall(env, url, slug, name, args, lic));
    const m = path.match(/^\/([a-z0-9-]+)\/mcp(\/.*)?$/) || path.match(/^\/\.well-known\/oauth-protected-resource\/([a-z0-9-]+)\/mcp$/);
    if (m && resources[m[1]]) {
      const res = await resources[m[1]].fetch(request, env, ctx);
      if (res.status === 401 && request.method === "GET" && (request.headers.get("accept") || "").includes("text/html")) {
        const slug = m[1], mcpUrl = `${origin(env)}/${slug}/mcp`, guide = slug === "despacho" ? "/asesorias/#conector" : `/${slug}/`;
        return page(`Conector ${NAMES[slug] || slug}`, `<h1>Conector ${esc(NAMES[slug] || slug)}</h1>
<p>Esta dirección es un <b>conector MCP</b> para pegar dentro de Claude (no se abre directamente en el navegador).</p>
<label for="mcp-url"><b>URL del conector</b></label>
<input id="mcp-url" value="${esc(mcpUrl)}" readonly onclick="this.select()">
<p class="muted" style="margin-top:12px"><b>Cómo conectarlo en Claude:</b><br>1. Abre Claude → <b>Ajustes (Settings) → Conectores (Connectors)</b>.<br>2. Pulsa <b>Añadir conector personalizado (Add custom connector)</b> y pega esta URL.<br>3. Escribe tu correo y el código de 6 dígitos que recibirás.</p>
<div class="row">
  <button type="button" class="btn btn-primary" style="order:2" onclick="navigator.clipboard.writeText('${esc(mcpUrl)}');this.textContent='URL copiada'">Copiar URL</button>
  <a class="btn" href="${esc(guide)}">Ver guía</a>
</div>`, new Headers(res.headers), 401);
      }
      return res;
    }
    if (path.startsWith("/oauth/") || path.startsWith("/.well-known/oauth-")) return as.fetch(request, env, ctx);
    return api.fetch(request, env, ctx);
  },
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(daily(env));
  },
};
