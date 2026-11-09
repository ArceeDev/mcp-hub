import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { bindLicense, issueTrial, licensesFor, openSession, readSession, startEmailLogin, verifyEmailCode } from "../src/emailauth.js";
import { fakeD1, mockFetch } from "./helpers.js";

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
const req = (ip = "203.0.113.7") => new Request("https://mcp.keyflint.dev/authorize", { headers: { "cf-connecting-ip": ip } });
const LIC = "LIC-eyJhbGciOiJFZERTQSJ9.payload.sig";
const env = () => ({ USAGE_DB: fakeD1(), OAUTH_KV: fakeKV(), RESEND_API_KEY: "re_x", KEYFLINT_ADMIN_KEY: "adm" });

// Captura el código enviado por Resend.
function mailer(extra = () => ({})) {
  const sent = [];
  m = mockFetch((url, init) => {
    if (url.includes("resend.com")) { sent.push(JSON.parse(init.body).text.match(/\d{6}/)[0]); return {}; }
    return extra(url, init);
  });
  return sent;
}

test("sin RESEND_API_KEY no hay acceso por correo (falla cerrado)", async () => {
  const e = env(); delete e.RESEND_API_KEY;
  const r = await startEmailLogin(e, req(), "ana@despacho.es");
  assert.equal(r.status, 503);
});

test("el código correcto verifica y es de un solo uso", async () => {
  const e = env(), sent = mailer();
  assert.ok((await startEmailLogin(e, req(), "ana@despacho.es")).ok);
  assert.equal(sent.length, 1);
  assert.ok((await verifyEmailCode(e, "ana@despacho.es", sent[0])).ok);
  const again = await verifyEmailCode(e, "ana@despacho.es", sent[0]);
  assert.equal(again.ok, undefined);
  assert.equal(again.expired, true);
});

test("el código no vale para otro correo", async () => {
  const e = env(), sent = mailer();
  await startEmailLogin(e, req(), "ana@despacho.es");
  assert.equal((await verifyEmailCode(e, "victima@despacho.es", sent[0])).ok, undefined);
});

test("5 fallos invalidan el código aunque luego se acierte", async () => {
  const e = env(), sent = mailer();
  await startEmailLogin(e, req(), "ana@despacho.es");
  const wrong = sent[0] === "000000" ? "111111" : "000000";
  for (let i = 0; i < 4; i++) assert.equal((await verifyEmailCode(e, "ana@despacho.es", wrong)).status, 400);
  const fifth = await verifyEmailCode(e, "ana@despacho.es", wrong);
  assert.equal(fifth.status, 429);
  assert.equal((await verifyEmailCode(e, "ana@despacho.es", sent[0])).expired, true);
});

test("límite de códigos por correo y por IP", async () => {
  const e = env(); mailer();
  for (let i = 0; i < 5; i++) assert.ok((await startEmailLogin(e, req(), "ana@despacho.es")).ok);
  assert.equal((await startEmailLogin(e, req(), "ana@despacho.es")).status, 429);
  for (let i = 0; i < 5; i++) await startEmailLogin(e, req(), `x${i}@despacho.es`);
  assert.equal((await startEmailLogin(e, req(), "otro@despacho.es")).status, 429);
});

test("si Resend falla se devuelve el cupo y no queda código", async () => {
  const e = env();
  m = mockFetch(() => ({ status: 500 }));
  assert.equal((await startEmailLogin(e, req(), "ana@despacho.es")).status, 502);
  assert.equal([...e.OAUTH_KV.map.keys()].filter((k) => k.startsWith("otp:")).length, 0);
  const n = e.USAGE_DB.raw.prepare("SELECT SUM(n) s FROM hub_limits").get().s;
  assert.equal(n, 0);
});

test("prueba: una por correo para siempre y queda enlazada al correo verificado", async () => {
  const e = env();
  m = mockFetch(() => ({ body: { data: { license_key: LIC } } }));
  const r = await issueTrial(e, req(), "ana@despacho.es");
  assert.equal(r.license, LIC);
  assert.deepEqual((await licensesFor(e, "ana@despacho.es")).map((l) => l.key), [LIC]);
  assert.equal((await issueTrial(e, req("198.51.100.1"), "ana@despacho.es")).status, 409);
});

test("las listas antiguas sin verificar (email_licenses:) se ignoran", async () => {
  const e = env();
  await e.OAUTH_KV.put("email_licenses:ana@despacho.es", JSON.stringify([{ key: LIC }]));
  assert.deepEqual(await licensesFor(e, "ana@despacho.es"), []);
  await bindLicense(e, "ana@despacho.es", { key: LIC });
  assert.equal((await licensesFor(e, "ANA@despacho.es ")).length, 1);
});

test("sesión verificada: token aleatorio, formato estricto", async () => {
  const e = env();
  const t = await openSession(e, "ana@despacho.es");
  assert.match(t, /^[0-9a-f]{48}$/);
  assert.equal(await readSession(e, t), "ana@despacho.es");
  assert.equal(await readSession(e, "ana@despacho.es"), "");
});


test("licensesFor recupera licencias activas del gateway si KV está vacío y las cachea", async () => {
  const e = env();
  m = mockFetch((url) => {
    if (url.includes("/api/v1/licenses/by-customer")) {
      return { body: { success: true, data: [{ key: LIC, tier: "pro", name: "Licencia PRO (3 puestos)" }] } };
    }
    return { status: 404 };
  });
  const list = await licensesFor(e, "cliente@despacho.es");
  assert.equal(list.length, 1);
  assert.equal(list[0].key, LIC);
  assert.equal(list[0].tier, "pro");

  // Al restaurar mockFetch (sin red), debe responder desde el cache KV
  m.restore();
  m = null;
  const cached = await licensesFor(e, "cliente@despacho.es");
  assert.equal(cached.length, 1);
  assert.equal(cached[0].key, LIC);
});
