import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";

// Un "*/" dentro de un comentario dejó /lote/ sin convertidor: todo script del navegador debe parsear.
test("los scripts de assets/ son JavaScript válido", () => {
  for (const f of readdirSync("assets").filter((n) => n.endsWith(".js"))) {
    const r = spawnSync(process.execPath, ["--check", "assets/" + f], { encoding: "utf8" });
    assert.equal(r.status, 0, f + ": " + r.stderr);
  }
});

test("el lote acepta extractos PDF y los envía a pdf_bank_to_journal", async () => {
  const { readFileSync } = await import("node:fs");
  const js = readFileSync("assets/lote.js", "utf8");
  assert.match(js, /var EXTS = \[[^\]]*"\.pdf"/);
  assert.match(js, /\.pdf"\) return \["contabridge", "pdf_bank_to_journal"\]/);
  assert.match(js, /pdf_bank_to_journal: 3/);
});

test("el visor Norma 43 valida saldos y totales sin red", async () => {
  const { readFileSync } = await import("node:fs");
  const js = readFileSync("assets/visor.js", "utf8");
  assert.doesNotMatch(js, /fetch\(|XMLHttpRequest|sendBeacon/);
  const rec = (s) => s.padEnd(80);
  const r11 = "112100041802000513322610012610312" + String(150000).padStart(14, "0") + "9783";
  const r22 = "22    0418" + "261002261002" + "01" + "000" + "2" + String(20000).padStart(14, "0");
  const r33 = "3321000418" + "0200051332" + "00000" + "00000000000000" + "00001" + String(20000).padStart(14, "0") + "2" + String(170000).padStart(14, "0") + "978";
  const text = [r11, r22, r33].map(rec).join("\n");
  globalThis.document = { querySelector: () => ({ addEventListener() {}, hidden: false, querySelector: () => null }) };
  globalThis.window = {};
  (0, eval)(js);
  const a = window.__visorN43.parse(text).accts[0];
  assert.equal(a.mov.length, 1);
  assert.deepEqual(a.ok.map((x) => x[0]), [true, true, true]);
  const bad = window.__visorN43.parse(text.replace(String(170000).padStart(14, "0"), String(170001).padStart(14, "0"))).accts[0];
  assert.ok(bad.ok.some((x) => !x[0]));
});

test("el validador IBAN, NIF, NIE, CIF y SEPA funciona en el navegador sin red", async () => {
  const { readFileSync } = await import("node:fs");
  const js = readFileSync("assets/validador.js", "utf8");
  assert.doesNotMatch(js, /fetch\(|XMLHttpRequest|sendBeacon/);
  globalThis.document = { querySelector: () => null };
  globalThis.window = {};
  (0, eval)(js);
  const v = window.__validador;
  assert.equal(v.validateOne("ES9121000418450200051332").valid, true);
  assert.equal(v.validateOne("ES9121000418440200051332").valid, false); // falla DC interno aunque cambies digitos
  assert.equal(v.validateOne("B84372291").valid, true);
  assert.equal(v.validateOne("B84372295").valid, false);
  assert.equal(v.validateOne("12345678Z").valid, true);
  assert.equal(v.validateOne("X0000001R").valid, true);
  assert.equal(v.validateOne("ES14000B84372291").valid, true);
  assert.equal(v.validateOne("ES99000B84372291").valid, false);
});
