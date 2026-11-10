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
