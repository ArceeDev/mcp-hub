import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import api from "../src/worker.js";
import { fakeD1, mockFetch, post } from "./helpers.js";

let m;
afterEach(() => m && m.restore());

const LIC = "LIC-eyJhbGciOiJFZERTQSJ9.payload.sig";
const ok = () => ({ body: { success: true, data: { checkout_url: "https://checkout.stripe.com/c/pay/cs_live_x", credits: 814 } } });
const get = (path) => new Request("https://mcp.keyflint.dev" + path, { headers: { "cf-connecting-ip": "203.0.113.7" } });

test("crea la recarga en el gateway con céntimos y vuelta a /saldo/", async () => {
  m = mockFetch(ok);
  const res = await api.fetch(post("/api/recarga", { license: LIC, amount: 37, currency: "eur", waiver: true }), { USAGE_DB: fakeD1() });
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { ok: true, url: "https://checkout.stripe.com/c/pay/cs_live_x", credits: 814 });
  assert.match(m.calls[0].url, /\/api\/v1\/billing\/topup$/);
  assert.deepEqual(m.calls[0].body, { license_key: LIC, amount_cents: 3700, currency: "eur", return_url: "https://mcp.keyflint.dev/saldo/" });
});

test("vuelve a la página del lote si la ruta es propia; si no, a /saldo/", async () => {
  const env = { USAGE_DB: fakeD1() };
  for (const [rp, want] of [["/lote/", "/lote/"], ["/csv-a-contasol/", "/csv-a-contasol/"], ["/en/batch/", "/en/batch/"],
    ["//evil.example/", "/saldo/"], ["https://evil.example/", "/saldo/"], ["/lote/?x=1", "/saldo/"], ["/../", "/saldo/"], ["/lote", "/saldo/"], [42, "/saldo/"]]) {
    m = mockFetch(ok);
    await api.fetch(post("/api/recarga", { license: LIC, amount: 10, waiver: true, return_path: rp }), env);
    assert.equal(m.calls[0].body.return_url, "https://mcp.keyflint.dev" + want, String(rp));
    m.restore(); m = null;
  }
});

test("valida importe, licencia, moneda y la casilla de desistimiento sin llamar al gateway", async () => {
  m = mockFetch(ok);
  const env = { USAGE_DB: fakeD1() };
  for (const b of [
    { license: LIC, amount: 4, waiver: true }, { license: LIC, amount: 501, waiver: true },
    { license: LIC, amount: 7.5, waiver: true }, { license: LIC, amount: "20", waiver: true },
    { license: "x", amount: 20, waiver: true }, { license: LIC, amount: 20, currency: "gbp", waiver: true },
    { license: LIC, amount: 20 },
  ]) assert.equal((await api.fetch(post("/api/recarga", b), env)).status, 400, JSON.stringify(b));
  assert.equal(m.calls.length, 0);
});

test("rechaza otro origen", async () => {
  m = mockFetch(ok);
  const res = await api.fetch(post("/api/recarga", { license: LIC, amount: 20, waiver: true }, "1.1.1.1", { origin: "https://evil.example" }), {});
  assert.equal(res.status, 403);
});

test("límite por IP y día; un fallo del gateway no gasta cupo", async () => {
  const env = { USAGE_DB: fakeD1(), TOPUP_PER_IP_DAY: "2" };
  m = mockFetch(() => ({ status: 502, body: {} }));
  assert.equal((await api.fetch(post("/api/recarga", { license: LIC, amount: 20, waiver: true }), env)).status, 502);
  m.restore();
  m = mockFetch(ok);
  for (let i = 0; i < 2; i++) assert.equal((await api.fetch(post("/api/recarga", { license: LIC, amount: 20, waiver: true }), env)).status, 200);
  assert.equal((await api.fetch(post("/api/recarga", { license: LIC, amount: 20, waiver: true }), env)).status, 429);
});

test("traduce los errores del gateway", async () => {
  for (const [st, want] of [[404, 404], [409, 409], [429, 429], [422, 400], [500, 502]]) {
    m = mockFetch(() => ({ status: st, body: { success: false } }));
    const res = await api.fetch(post("/api/recarga", { license: LIC, amount: 20, waiver: true }), { USAGE_DB: fakeD1() });
    assert.equal(res.status, want, String(st));
    m.restore(); m = null;
  }
});

test("estado de la recarga a la vuelta de Stripe", async () => {
  m = mockFetch(() => ({ body: { success: true, data: { status: "applied", credits: 814, credit_balance: 839 } } }));
  const res = await api.fetch(get("/api/recarga?session=cs_live_abcdefghijkl"), {});
  assert.deepEqual(await res.json(), { ok: true, status: "applied", credits: 814, balance: 839 });
  assert.match(m.calls[0].url, /\/api\/v1\/billing\/topup\/cs_live_abcdefghijkl$/);
  assert.equal((await api.fetch(get("/api/recarga?session=nope"), {})).status, 400);
});
