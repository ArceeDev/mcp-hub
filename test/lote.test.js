import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";

test("carpeta vigilada: cobra por fichero OK, no reintenta en bucle y autoarranque válido", () => {
  const py = process.platform === "win32" ? "python" : "python3";
  const r = spawnSync(py, ["test/lote_check.py"], { encoding: "utf8" });
  if (r.error?.code === "ENOENT") return; // sin Python en la máquina: se omite
  assert.equal(r.status, 0, (r.stdout || "") + (r.stderr || ""));
  assert.match(r.stdout, /lote OK/);
});
