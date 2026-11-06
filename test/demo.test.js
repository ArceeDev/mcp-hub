import assert from "node:assert/strict";
import { test } from "node:test";
import { demo, unwrap } from "../src/demo.js";
import { fakeD1, post } from "./helpers.js";

const URL0 = new URL("https://mcp.keyflint.dev/");
const rpc = (structured) => JSON.stringify({ jsonrpc: "2.0", id: 1, result: { structuredContent: structured, content: [] } });

function env(extra = {}) {
  return { USAGE_DB: fakeD1(), HUB_DEMO_LICENSE: "LIC-hub-demo-123", ...extra };
}

test("web-intel: llama a read_url con la licencia del hub y recorta la salida", async () => {
  const calls = [];
  const call = async (slug, name, args, lic) => {
    calls.push({ slug, name, args, lic });
    return rpc({ url: args.url, title: "Hola", word_count: 3, markdown: "x".repeat(9000), billing: { credits_charged: 1 } });
  };
  const res = await demo(post("/api/demo/web-intel", { url: "example.com" }), env(), URL0, "web-intel", call);
  const d = await res.json();
  assert.equal(res.status, 200);
  assert.equal(calls[0].name, "read_url");
  assert.equal(calls[0].args.url, "https://example.com/");
  assert.equal(calls[0].lic, "LIC-hub-demo-123");
  assert.equal(d.result.markdown.length, 6000);
  assert.equal("billing" in d.result, false);
});

test("valida entradas antes de gastar cupo", async () => {
  const e = env();
  const call = async () => { throw new Error("no debería llamarse"); };
  assert.equal((await demo(post("/x", { url: "ftp://a.b" }), e, URL0, "web-intel", call)).status, 400);
  assert.equal((await demo(post("/x", { content: "" }), e, URL0, "norma43", call)).status, 400);
  assert.equal((await demo(post("/x", { content: "a;b\n", target: "sap" }), e, URL0, "contabridge", call)).status, 400);
  assert.equal((await demo(post("/x", {}), e, URL0, "verifactu", call)).status, 404);
  assert.equal(e.USAGE_DB.raw.prepare("SELECT COUNT(*) c FROM hub_limits").get().c, 0);
});

test("límite por IP y día; un error del servidor no gasta cupo", async () => {
  const e = env({ DEMO_PER_IP_DAY: "2" });
  const bad = async () => JSON.stringify({ jsonrpc: "2.0", id: 1, result: { isError: true, content: [{ type: "text", text: "Fichero no válido" }] } });
  const good = async () => rpc({ valid: true, summary: { movements: 2 }, accounts: [] });
  const r0 = await demo(post("/x", { content: "11..." }), e, URL0, "norma43", bad);
  assert.equal(r0.status, 422);
  assert.match((await r0.json()).error, /no válido/);
  for (let i = 0; i < 2; i++) assert.equal((await demo(post("/x", { content: "11..." }), e, URL0, "norma43", good)).status, 200);
  const r3 = await demo(post("/x", { content: "11..." }), e, URL0, "norma43", good);
  assert.equal(r3.status, 429);
  assert.equal((await demo(post("/x", { content: "11..." }, "198.51.100.2"), e, URL0, "norma43", good)).status, 200);
});

test("tope global diario", async () => {
  const e = env({ DEMO_DAILY_CAP: "1" });
  const good = async () => rpc({ format: "a3", filename: "SUENLACE.DAT", content: "x" });
  assert.equal((await demo(post("/x", { content: "a;b\n" }), e, URL0, "contabridge", good)).status, 200);
  assert.equal((await demo(post("/x", { content: "a;b\n" }, "198.51.100.3"), e, URL0, "contabridge", good)).status, 429);
});

test("sin licencia interna la demo está apagada", async () => {
  const res = await demo(post("/x", { url: "a.com" }), { USAGE_DB: fakeD1() }, URL0, "web-intel", async () => "");
  assert.equal(res.status, 503);
});

test("unwrap entiende result.result y errores JSON-RPC", () => {
  assert.deepEqual(unwrap(JSON.stringify({ result: { structuredContent: { result: { a: 1 } } } })), { ok: true, data: { a: 1 } });
  assert.equal(unwrap(JSON.stringify({ error: { message: "Sin saldo" } })).error, "Sin saldo");
  assert.equal(unwrap("<html>").ok, false);
});
