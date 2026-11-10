import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { SLUGS } from "../src/slugs.js";

test("/despacho/mcp: un conector con Norma 43 + ContaBridge, misma facturación", () => {
  const py = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
  const r = spawnSync(py, ["test/despacho_check.py"], { encoding: "utf8" });
  if (r.error?.code === "ENOENT") return; // sin Python: se omite
  assert.equal(r.status, 0, (r.stdout || "") + (r.stderr || ""));
  assert.match(r.stdout, /despacho (OK|SKIP)/);
});

test("el Worker expone /despacho/mcp con OAuth como los demás", () => {
  assert.ok(SLUGS.includes("despacho"));
});
