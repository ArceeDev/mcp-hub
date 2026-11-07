// mcp.keyflint.dev: web estática, API mínima (/api/*) y los MCP remotos con OAuth.
//
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
import { demo } from "./demo.js";
import { status } from "./status.js";

export const SLUGS = ["web-intel", "norma43", "contabridge", "verifactu", "dataclean"];
const NAMES = { "web-intel": "Web Intel", norma43: "Norma 43", contabridge: "ContaBridge", verifactu: "VeriFactu",
  dataclean: "DataClean" };
const SCOPE = "mcp";
const LICENSE_RE = /^LIC-[A-Za-z0-9._~+\/=-]{6,1024}$/;
const INSTANCES = 1; // 1 contenedor primario caliente evita 3x cold-starts; escalable con MCP_INSTANCES
const QUIET = new Set(["credits_balance", "pricing"]); // gratis y frecuentes: no ensucian el historial

export class McpRuntime extends Container {
  defaultPort = 8080;
  sleepAfter = "10m";
  enableInternet = true; // Web Intel lee webs; todos cobran contra licenses.keyflint.dev
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
.auth .logo img{width:28px;height:28px}</style></head><body><main class="auth"><div class="logo"><img src="/assets/flint-icon.svg" alt="">Flint <span class="muted">by KeyFlint</span></div>
<div class="card">${body}</div></main></body></html>`, { status, headers });
}

function consentForm(details, handle, error = "") {
  const app = esc(details.clientName || "Una aplicación");
  const who = details.clientDomain
    ? `Publicada por <b>${esc(details.clientDomain)}</b>.`
    : "La aplicación se registró sola; su nombre no está verificado.";
  return `<h1>Conectar ${app}</h1>
<p>${who} El acceso se enviará a <b>${esc(details.redirectHost)}</b>.</p>
${details.redirectIsLoopback ? '<p class="warn">Esto envía el acceso a una aplicación de tu ordenador. Sigue solo si acabas de iniciar la conexión desde ella.</p>' : ""}
<p class="muted">Podrá usar los servidores MCP de KeyFlint con tu licencia y gastar sus créditos. Puedes revocarlo cuando quieras.</p>
<form method="post">
<input type="hidden" name="handle" value="${esc(handle)}">
<label for="lic"><b>Tu licencia</b></label>
<input id="lic" name="license" autocomplete="off" spellcheck="false" placeholder="LIC-…" required>
${error ? `<p class="err">${esc(error)}</p>` : ""}
<p class="muted">¿No tienes? <a href="/probar/" target="_blank" rel="noopener">Consigue una gratis</a> (25 créditos al instante) o <a href="/saldo/#recuperar" target="_blank" rel="noopener">recupérala por correo</a>.</p>
<div class="row"><button class="btn" name="decision" value="deny" formnovalidate>Cancelar</button>
<button class="btn btn-primary" name="decision" value="approve">Conectar</button></div>
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
    if (form.get("decision") !== "approve") {
      const denied = await oauth.denyConsent(request, handle);
      return new Response(null, { status: 302, headers: denied.headers });
    }
    // approveConsent consume el formulario; si la licencia no vale, se abre otro con la misma petición validada.
    const approved = await oauth.approveConsent(request, handle, { scope: [SCOPE, "offline_access"] });
    const license = String(form.get("license") || "").trim();
    const state = LICENSE_RE.test(license) ? await licenseExists(env, license) : "format";
    if (state !== "ok") {
      const msg = state === "format" ? "Eso no parece una licencia. Empieza por LIC- y viene en el correo de compra."
        : state === "down" ? "KeyFlint no responde ahora mismo. Inténtalo en un minuto."
          : "No encontramos esa licencia. Revisa que esté completa.";
      const details = await oauth.describeConsent(approved.request);
      const again = await oauth.beginConsent(approved.request);
      return page("Licencia", consentForm(details, again.handle, msg), again.headers, 400);
    }
    const { redirectTo } = await oauth.completeAuthorization({
      request: approved.request,
      userId: await userId(license),
      metadata: { connected: new Date().toISOString() },
      scope: approved.request.scope,
      props: { license },
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
    if (path === "/api/estado" && request.method === "GET")
      return status(env, ctx, SLUGS, () => upstreamFetch(env, new URL("http://mcp/healthz"), new Request("http://mcp/healthz")));
    const dm = path.match(/^\/api\/demo\/([a-z0-9-]+)$/);
    if (dm && request.method === "POST") return demo(request, env, url, dm[1], (slug, name, args, lic) => demoCall(env, url, slug, name, args, lic));
    const m = path.match(/^\/([a-z0-9-]+)\/mcp(\/.*)?$/) || path.match(/^\/\.well-known\/oauth-protected-resource\/([a-z0-9-]+)\/mcp$/);
    if (m && resources[m[1]]) return resources[m[1]].fetch(request, env, ctx);
    if (path.startsWith("/oauth/") || path.startsWith("/.well-known/oauth-")) return as.fetch(request, env, ctx);
    return api.fetch(request, env, ctx);
  },
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(daily(env));
  },
};
