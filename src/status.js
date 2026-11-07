// Estado público (/api/estado): servidor de licencias + contenedor de herramientas.
// Se cachea 60 s para no despertar el contenedor en cada visita.
const within = (p, ms) => Promise.race([p, new Promise((r) => setTimeout(() => r(null), ms))]).catch(() => null);

export async function status(env, ctx, slugs, runtimeHealth) {
  const cache = globalThis.caches && caches.default;
  const key = new Request("https://mcp-hub.internal/api/estado");
  const hit = cache && (await cache.match(key));
  if (hit) return hit;
  const gwUrl = (env.GATEWAY_URL || "https://licenses.keyflint.dev").replace(/\/$/, "") + "/healthz";
  const [gw, rt] = await Promise.all([
    within(fetch(gwUrl, { headers: { "user-agent": "mcp-hub-worker" } }), 8000),
    within(Promise.resolve().then(runtimeHealth), 20000),
  ]);
  const servers = rt && rt.ok ? ((await rt.json().catch(() => ({}))).servers || []) : [];
  const tools = Object.fromEntries(slugs.map((s) => [s, servers.includes(s)]));
  const licenses = Boolean(gw && gw.ok);
  const body = { ok: licenses && Object.values(tools).every(Boolean), licenses, tools, checked: new Date().toISOString() };
  const res = new Response(JSON.stringify(body), {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=60" },
  });
  if (cache) ctx.waitUntil(cache.put(key, res.clone()));
  return res;
}
