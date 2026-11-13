import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";

// D1 mínimo sobre node:sqlite (prepare/bind/first/run/all) con las migraciones reales.
export function fakeD1() {
  const db = new DatabaseSync(":memory:");
  for (const f of ["0001_usage.sql", "0002_hub_limits.sql", "0003_visits.sql"]) db.exec(readFileSync(new URL(`../migrations/${f}`, import.meta.url), "utf8"));
  const wrap = (sql, args = []) => ({
    bind: (...a) => wrap(sql, a),
    first: async () => db.prepare(sql).get(...args) ?? null,
    all: async () => ({ results: db.prepare(sql).all(...args) }),
    run: async () => db.prepare(sql).run(...args),
  });
  return { prepare: (sql) => wrap(sql), raw: db };
}

export function post(path, body, ip = "203.0.113.7", headers = {}) {
  return new Request("https://mcp.keyflint.dev" + path, {
    method: "POST",
    headers: { "content-type": "application/json", "cf-connecting-ip": ip, origin: "https://mcp.keyflint.dev", ...headers },
    body: JSON.stringify(body),
  });
}

// Sustituye fetch global por un gateway falso. handler(url, init) -> {status, body}.
export function mockFetch(handler) {
  const calls = [];
  const prev = globalThis.fetch;
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url: String(url), init, body: init.body ? JSON.parse(init.body) : null });
    const { status = 200, body = {} } = await handler(String(url), init);
    return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
  };
  return { calls, restore: () => { globalThis.fetch = prev; } };
}
