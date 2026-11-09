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
