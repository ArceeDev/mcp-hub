import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import api from "../src/worker.js";
import { fakeD1, mockFetch, post } from "./helpers.js";

let m;
afterEach(() => m && m.restore());

const LIC = "LIC-eyJhbGciOiJFZERTQSJ9.payload.sig";
const issueOk = () => ({ body: { success: true, data: { license_key: LIC, tier: "community" } } });

test("emite la licencia de prueba y la devuelve en pantalla", async () => {
  m = mockFetch(issueOk);
  const env = { USAGE_DB: fakeD1(), KEYFLINT_ADMIN_KEY: "adm" };
  const res = await api.fetch(post("/api/prueba", { email: "Ana@Example.com" }), env);
  const d = await res.json();
  assert.equal(res.status, 200);
  assert.deepEqual(d, { ok: true, license: LIC, tier: "community", credits: 25 });
  assert.match(m.calls[0].url, /\/api\/v1\/licenses\/issue$/);
  assert.equal(m.calls[0].init.headers["x-admin-key"], "adm");
  assert.equal(m.calls[0].body.tier, "community");
  assert.equal(m.calls[0].body.metadata.trial, true);
});

test("una sola licencia por correo, aunque cambien mayúsculas o la IP", async () => {
  m = mockFetch(issueOk);
  const env = { USAGE_DB: fakeD1(), KEYFLINT_ADMIN_KEY: "adm" };
  assert.equal((await api.fetch(post("/api/prueba", { email: "a@b.io" }), env)).status, 200);
  const again = await api.fetch(post("/api/prueba", { email: "A@B.io" }, "198.51.100.9"), env);
  assert.equal(again.status, 409);
  assert.equal((await again.json()).used, true);
  assert.equal(m.calls.length, 1);
});

test("límite por IP y día", async () => {
  m = mockFetch(issueOk);
  const env = { USAGE_DB: fakeD1(), KEYFLINT_ADMIN_KEY: "adm", TRIAL_PER_IP_DAY: "2" };
  for (const e of ["1@x.io", "2@x.io"]) assert.equal((await api.fetch(post("/api/prueba", { email: e }), env)).status, 200);
  assert.equal((await api.fetch(post("/api/prueba", { email: "3@x.io" }), env)).status, 429);
  assert.equal((await api.fetch(post("/api/prueba", { email: "3@x.io" }, "198.51.100.1"), env)).status, 200);
});

test("si KeyFlint falla, el correo y la IP recuperan su cupo", async () => {
  let fail = true;
  m = mockFetch(() => (fail ? { status: 500, body: {} } : issueOk()));
  const env = { USAGE_DB: fakeD1(), KEYFLINT_ADMIN_KEY: "adm", TRIAL_PER_IP_DAY: "1" };
  assert.equal((await api.fetch(post("/api/prueba", { email: "x@y.io" }), env)).status, 502);
  fail = false;
  assert.equal((await api.fetch(post("/api/prueba", { email: "x@y.io" }), env)).status, 200);
});

test("sin clave de administración usa el envío por correo de KeyFlint", async () => {
  m = mockFetch(() => ({ body: { success: true } }));
  const env = { USAGE_DB: fakeD1() };
  const d = await (await api.fetch(post("/api/prueba", { email: "c@d.io" }), env)).json();
  assert.deepEqual(d, { ok: true, emailed: true });
  assert.match(m.calls[0].url, /\/api\/v1\/billing\/trial$/);
  assert.equal(JSON.stringify(d).includes("LIC-"), false);
});

test("rechaza otro origen y correos no válidos", async () => {
  m = mockFetch(issueOk);
  const env = { USAGE_DB: fakeD1(), KEYFLINT_ADMIN_KEY: "adm" };
  assert.equal((await api.fetch(post("/api/prueba", { email: "a@b.io" }, undefined, { origin: "https://evil.example" }), env)).status, 403);
  assert.equal((await api.fetch(post("/api/prueba", { email: "nope" }), env)).status, 400);
  assert.equal(m.calls.length, 0);
});
