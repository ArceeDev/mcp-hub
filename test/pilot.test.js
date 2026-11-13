import assert from "node:assert/strict";
import { test } from "node:test";
import api from "../src/worker.js";
import { fakeD1, mockFetch, post } from "./helpers.js";

const ok = { email: "Ana@Despacho.es", nombre: "Ana", despacho: "Asesoría Ana", programa: "contasol", clientes: "11-30", telefono: "600 000 000", mensaje: "<b>hola</b>", acepto: true, origen: "Facebook" };
const send = (env, body, ip = "1.1.1.1") => api.fetch(post("/api/piloto", body, ip), env);

test("piloto: guarda la solicitud y avisa a Arcee con reply-to del despacho", async () => {
  const env = { USAGE_DB: fakeD1(), RESEND_API_KEY: "re_x", REPORT_EMAIL: "arcee@example.com" };
  const m = mockFetch(async () => ({ body: { id: "e1" } }));
  try {
    const r = await send(env, ok);
    assert.equal(r.status, 200);
    assert.deepEqual(await r.json(), { ok: true });
    const row = env.USAGE_DB.raw.prepare("SELECT * FROM pilots").get();
    assert.equal(row.email, "ana@despacho.es");
    assert.equal(row.origen, "facebook");
    assert.ok(!row.mensaje.includes("<"));
    assert.equal(m.calls.length, 1);
    assert.deepEqual(m.calls[0].body.to, ["arcee@example.com"]);
    assert.equal(m.calls[0].body.reply_to, "ana@despacho.es");
    // mismo correo: no duplica ni reenvía
    await send(env, ok, "2.2.2.2");
    assert.equal(env.USAGE_DB.raw.prepare("SELECT COUNT(*) AS n FROM pilots").get().n, 1);
    assert.equal(m.calls.length, 1);
  } finally { m.restore(); }
});

test("piloto: exige permiso, programa válido y descarta bots", async () => {
  const env = { USAGE_DB: fakeD1() };
  assert.equal((await send(env, { ...ok, acepto: false })).status, 400);
  assert.equal((await send(env, { ...ok, programa: "sap" })).status, 400);
  assert.equal((await send(env, { ...ok, email: "no" })).status, 400);
  assert.equal((await send(env, { ...ok, web: "http://spam" })).status, 200);
  assert.equal(env.USAGE_DB.raw.prepare("SELECT COUNT(*) AS n FROM pilots").get().n, 0);
  const cross = post("/api/piloto", ok, "3.3.3.3", { origin: "https://evil.example" });
  assert.equal((await api.fetch(cross, env)).status, 403);
});

test("embudo: /ev/<paso> no cuenta como visita y sale aparte en el informe", async () => {
  const env = { USAGE_DB: fakeD1(), KEYFLINT_ADMIN_KEY: "adm" };
  const v = (body) => { const r = post("/api/v", body, "4.4.4.4", { "user-agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/130" }); Object.defineProperty(r, "cf", { value: { country: "ES", asn: 3352 } }); return api.fetch(r, env); };
  await v({ p: "/asesorias/", e: 1 });
  await v({ p: "/ev/licencia-ok", e: 0 });
  await v({ p: "/ev/conversion-ok-contasol", e: 0 });
  await v({ p: "/ev/conversion-ok-contasol", e: 0 });
  const body = await (await api.fetch(new Request("https://mcp.keyflint.dev/api/admin/visitas?dias=7", { headers: { "x-admin-key": "adm" } }), env)).json();
  assert.equal(body.total.vistas, 1);
  assert.deepEqual(body.embudo[0], { k: "conversion-ok-contasol", n: 2 });
  assert.ok(!body.paginas.some((p) => p.k.startsWith("/ev/")));
});
