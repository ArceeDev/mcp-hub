import assert from "node:assert/strict";
import { test } from "node:test";
import api from "../src/worker.js";
import { refHost } from "../src/visits.js";
import { fakeD1, post } from "./helpers.js";

const mkEnv = () => ({ USAGE_DB: fakeD1(), KEYFLINT_ADMIN_KEY: "adm" });
const send = (env, body, ip, extra = {}) => {
  const r = post("/api/v", body, ip, { "user-agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/130", ...extra });
  Object.defineProperty(r, "cf", { value: { country: extra.cc || "ES", asn: 3352 } });
  return api.fetch(r, env);
};
const report = (env, key = "adm") => api.fetch(new Request("https://mcp.keyflint.dev/api/admin/visitas?dias=7", { headers: { "x-admin-key": key } }), env);

test("visitas: agrega por ruta/origen/UTM/país sin guardar IP ni query", async () => {
  const env = mkEnv();
  assert.equal((await send(env, { p: "/visor-norma-43/", r: "https://www.reddit.com/r/x?u=1", s: "Reddit", c: "dia-d", e: 1 }, "1.1.1.1")).status, 204);
  await send(env, { p: "/visor-norma-43/", r: "https://reddit.com/r/y", s: "reddit", c: "dia-d", e: 1 }, "2.2.2.2");
  await send(env, { p: "/precios/", r: "https://mcp.keyflint.dev/", e: 0 }, "2.2.2.2", { cc: "MX" });
  await send(env, { p: "/x?email=a@b.c", r: "javascript:alert(1)", s: "<script>", e: 1 }, "3.3.3.3");
  const rows = env.USAGE_DB.raw.prepare("SELECT * FROM visits ORDER BY n DESC").all();
  assert.equal(rows[0].n, 2);
  assert.deepEqual([rows[0].path, rows[0].ref, rows[0].src, rows[0].camp, rows[0].country], ["/visor-norma-43/", "reddit.com", "reddit", "dia-d", "ES"]);
  const dump = JSON.stringify(env.USAGE_DB.raw.prepare("SELECT * FROM visits").all());
  assert.ok(!dump.includes("1.1.1.1") && !dump.includes("email") && !dump.includes("script"));
  const body = await (await report(env)).json();
  assert.equal(body.total.vistas, 4);
  assert.equal(body.total.visitas, 3);
  assert.equal(body.paises[0].k, "ES");
  assert.equal(body.redes_asn[0].k, 3352);
  assert.equal(body.dispositivos[0].k, "d");
});

test("visitas: ignora bots, otros orígenes y exige clave para el informe", async () => {
  const env = mkEnv();
  await send(env, { p: "/" }, "1.1.1.1", { "user-agent": "Googlebot/2.1" });
  await send(env, { p: "/" }, "1.1.1.1", { origin: "https://evil.example" });
  await send(env, { p: "/" }, "1.1.1.1", { "user-agent": "" });
  assert.equal(env.USAGE_DB.raw.prepare("SELECT COUNT(*) c FROM visits").get().c, 0);
  assert.equal((await report(env, "nope")).status, 403);
  assert.equal((await report(env, "")).status, 403);
});

test("visitas: freno por IP y dominio propio no cuenta como origen", async () => {
  assert.equal(refHost("https://mcp.keyflint.dev/precios/", "mcp.keyflint.dev"), "");
  assert.equal(refHost("https://news.ycombinator.com/item?id=1", "mcp.keyflint.dev"), "news.ycombinator.com");
  const env = mkEnv();
  for (let i = 0; i < 305; i++) await send(env, { p: "/" }, "9.9.9.9");
  assert.equal(env.USAGE_DB.raw.prepare("SELECT SUM(n) s FROM visits").get().s, 300);
});
