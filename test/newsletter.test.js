import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import api from "../src/worker.js";
import { fakeD1, mockFetch, post } from "./helpers.js";

let m;
afterEach(() => m && m.restore());

function fakeKV() {
  const map = new Map();
  return {
    map,
    get: async (k, type) => (map.has(k) ? (type === "json" ? JSON.parse(map.get(k)) : map.get(k)) : null),
    put: async (k, v) => { map.set(k, v); },
    delete: async (k) => { map.delete(k); },
  };
}

const mkEnv = () => ({ USAGE_DB: fakeD1(), OAUTH_KV: fakeKV(), RESEND_API_KEY: "re_test", KEYFLINT_ADMIN_KEY: "adm" });

function captureConfirmLinks(extra = () => ({})) {
  const links = [];
  m = mockFetch((url, init) => {
    if (url.includes("resend.com")) {
      const body = JSON.parse(init.body);
      const match = body.text.match(/https:\/\/[^\s]+\/boletin\/confirmar\/\?token=([0-9a-f]{48})/);
      links.push({ email: body.to[0], token: match ? match[1] : null });
      return {};
    }
    return extra(url, init);
  });
  return links;
}

test("boletín: doble opt-in completo (alta, confirmación y baja en 1 clic)", async () => {
  const env = mkEnv(), sent = captureConfirmLinks();

  // 1. Alta inicial envía token y NO guarda aún en sub_mail:
  const res1 = await api.fetch(post("/api/boletin/alta", { email: "Asesoria@Despacho.es", source: "visor-n43" }), env);
  assert.equal(res1.status, 200);
  assert.deepEqual(await res1.json(), { ok: true });
  assert.equal(sent.length, 1);
  assert.ok(sent[0].token);
  const subsBefore = [...env.OAUTH_KV.map.keys()].filter((k) => k.startsWith("sub_mail:"));
  assert.equal(subsBefore.length, 0);

  // 2. Confirmar guarda sub_mail y unsub_token y quema el pending token:
  const res2 = await api.fetch(post("/api/boletin/confirmar", { token: sent[0].token }), env);
  assert.equal(res2.status, 200);
  assert.deepEqual(await res2.json(), { ok: true });
  const subKey = [...env.OAUTH_KV.map.keys()].find((k) => k.startsWith("sub_mail:"));
  assert.ok(subKey);
  const stored = JSON.parse(env.OAUTH_KV.map.get(subKey));
  assert.equal(stored.email, "asesoria@despacho.es");
  assert.equal(stored.source, "visor-n43");
  assert.match(stored.unsub_token, /^[0-9a-f]{48}$/);

  // Reusar token caducado/usado falla:
  const resReuse = await api.fetch(post("/api/boletin/confirmar", { token: sent[0].token }), env);
  assert.equal(resReuse.status, 400);

  // Volver a darse de alta ya confirmado no reenvía correo:
  const resAlready = await api.fetch(post("/api/boletin/alta", { email: "asesoria@despacho.es" }), env);
  assert.deepEqual(await resAlready.json(), { ok: true, already: true });
  assert.equal(sent.length, 1);

  // 3. Baja en 1 clic borra correo y token de baja:
  const res3 = await api.fetch(post("/api/boletin/baja", { token: stored.unsub_token }), env);
  assert.equal(res3.status, 200);
  assert.deepEqual(await res3.json(), { ok: true });
  assert.equal(env.OAUTH_KV.map.has(subKey), false);
});

test("boletín: falla cerrado sin Resend, rechaza otro origen y devuelve cupo si Resend cae", async () => {
  const noKey = mkEnv(); delete noKey.RESEND_API_KEY;
  assert.equal((await api.fetch(post("/api/boletin/alta", { email: "a@b.es" }), noKey)).status, 503);

  const env = mkEnv();
  assert.equal((await api.fetch(post("/api/boletin/alta", { email: "a@b.es" }, undefined, { origin: "https://evil.es" }), env)).status, 403);
  assert.equal((await api.fetch(post("/api/boletin/alta", { email: "malo" }), env)).status, 400);

  let fail = true;
  m = mockFetch((url) => {
    if (url.includes("resend.com")) return fail ? { status: 500, body: {} } : {};
    return {};
  });
  env.NEWSLETTER_PER_IP_DAY = "1";
  assert.equal((await api.fetch(post("/api/boletin/alta", { email: "x@despacho.es" }), env)).status, 502);
  fail = false;
  assert.equal((await api.fetch(post("/api/boletin/alta", { email: "x@despacho.es" }), env)).status, 200);
});

test("/api/prueba con newsletter: true inicia doble opt-in tras emitir licencia", async () => {
  const env = mkEnv();
  const LIC = "LIC-eyJhbGciOiJFZERTQSJ9.payload.sig";
  const sent = captureConfirmLinks(() => ({ body: { success: true, data: { license_key: LIC, tier: "community" } } }));

  const res = await api.fetch(post("/api/prueba", { email: "nuevo@despacho.es", newsletter: true }), env);
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { ok: true, license: LIC, tier: "community", credits: 25, newsletter_sent: true });
  assert.equal(sent.length, 1);
  assert.equal(sent[0].email, "nuevo@despacho.es");
});
