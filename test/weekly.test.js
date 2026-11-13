import assert from "node:assert/strict";
import { test } from "node:test";
import api from "../src/worker.js";
import { buildWeekly, weekly, weeklyText } from "../src/weekly.js";
import { fakeD1, mockFetch } from "./helpers.js";

const fakeKV = () => { const m = new Map(); return { get: async (k) => m.get(k) ?? null, put: async (k, v) => { m.set(k, v); } }; };
const NOW = Date.UTC(2026, 10, 16, 7); // lunes
const D = Math.floor(NOW / 86_400_000);

function seed(db) {
  const ins = "INSERT INTO visits (day,path,ref,src,med,camp,country,entry,dev,asn,n) VALUES (?,?,?,?,?,?,?,?,?,?,?)";
  db.raw.prepare(ins).run(D - 2, "/visor-norma-43/", "linkedin.com", "linkedin", "social", "dia-d", "ES", 1, "d", 3352, 4);
  db.raw.prepare(ins).run(D - 3, "/precios/", "", "", "", "", "ES", 0, "d", 3352, 3);
  db.raw.prepare(ins).run(D - 9, "/", "", "", "", "", "ES", 1, "d", 3352, 1); // semana anterior
  db.raw.prepare(ins).run(D, "/", "", "", "", "", "ES", 1, "d", 3352, 50); // hoy: fuera del informe
  const u = "INSERT INTO usage (lic,ts,slug,tool,ok,credits,ms) VALUES (?,?,?,?,?,?,?)";
  db.raw.prepare(u).run("a", (D - 1) * 86400, "norma43", "parse_norma43", 1, 1, 10);
  db.raw.prepare(u).run("b", (D - 1) * 86400, "norma43", "parse_norma43", 0, 0, 10);
  db.raw.prepare("INSERT INTO hub_limits (kind,k,day,n) VALUES ('trial_email','x',0,1),('trial_email','y',0,1),('trial_ip','z',?,1)").run(D);
}

test("semanal: agrega 7 días cerrados, compara con la anterior y no envía sin REPORT_EMAIL", async () => {
  const env = { USAGE_DB: fakeD1(), OAUTH_KV: fakeKV() };
  seed(env.USAGE_DB);
  const r = await buildWeekly(env, NOW);
  assert.equal(r.visitas.visitas, 4);
  assert.equal(r.visitas.vistas, 7);
  assert.equal(r.visitasPrev.visitas, 1);
  assert.equal(r.visitas.origenes[0].k, "linkedin.com");
  assert.equal(r.uso.llamadas, 2);
  assert.equal(r.uso.licencias_activas, 2);
  assert.equal(r.pruebasTotal, 2);
  assert.equal(r.pruebas, null);
  assert.match(weeklyText(r), /Visitas: 4 \(\+3/);
  const m = mockFetch(() => ({ status: 200 }));
  try {
    const out = await weekly(env, NOW);
    assert.equal(out.enviado, false);
    assert.equal(m.calls.length, 0);
  } finally { m.restore(); }
  env.USAGE_DB.raw.prepare("INSERT INTO hub_limits (kind,k,day,n) VALUES ('trial_email','w',0,1)").run();
  assert.equal((await buildWeekly(env, NOW + 7 * 86_400_000)).pruebas, 1);
});

test("semanal: envía por Resend a REPORT_EMAIL", async () => {
  const env = { USAGE_DB: fakeD1(), OAUTH_KV: fakeKV(), REPORT_EMAIL: "yo@example.com", RESEND_API_KEY: "k" };
  seed(env.USAGE_DB);
  const m = mockFetch(() => ({ status: 200, body: { id: "1" } }));
  try {
    const out = await weekly(env, NOW);
    assert.equal(out.enviado, true);
    assert.equal(m.calls[0].url, "https://api.resend.com/emails");
    assert.deepEqual(m.calls[0].body.to, ["yo@example.com"]);
    assert.match(m.calls[0].body.text, /Informe semanal Flint/);
  } finally { m.restore(); }
});

test("semanal: el endpoint exige x-admin-key", async () => {
  const env = { USAGE_DB: fakeD1(), OAUTH_KV: fakeKV(), KEYFLINT_ADMIN_KEY: "adm" };
  const bad = await api.fetch(new Request("https://mcp.keyflint.dev/api/admin/semanal", { headers: { "x-admin-key": "no" } }), env);
  assert.equal(bad.status, 403);
  const ok = await api.fetch(new Request("https://mcp.keyflint.dev/api/admin/semanal", { headers: { "x-admin-key": "adm" } }), env);
  const j = await ok.json();
  assert.equal(j.ok, true);
  assert.match(j.texto, /Informe semanal/);
});
