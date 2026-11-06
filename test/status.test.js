import assert from "node:assert/strict";
import { test } from "node:test";
import { status } from "../src/status.js";
import { mockFetch } from "./helpers.js";

const SLUGS = ["web-intel", "norma43"];
const ctx = { waitUntil() {} };
const health = (servers, ok = true) => async () => new Response(JSON.stringify({ servers }), { status: ok ? 200 : 503 });

test("todo bien: licencias y herramientas responden", async () => {
  const m = mockFetch(async () => ({ status: 200, body: { status: "ok" } }));
  try {
    const d = await (await status({}, ctx, SLUGS, health(["web-intel", "norma43"]))).json();
    assert.equal(d.ok, true);
    assert.equal(d.licenses, true);
    assert.deepEqual(d.tools, { "web-intel": true, norma43: true });
    assert.equal(m.calls[0].url, "https://licenses.keyflint.dev/healthz");
  } finally { m.restore(); }
});

test("marca la herramienta que falta y el gateway caído", async () => {
  const m = mockFetch(async () => ({ status: 503 }));
  try {
    const d = await (await status({}, ctx, SLUGS, health(["web-intel"]))).json();
    assert.equal(d.ok, false);
    assert.equal(d.licenses, false);
    assert.deepEqual(d.tools, { "web-intel": true, norma43: false });
  } finally { m.restore(); }
});

test("si el contenedor falla, todas las herramientas salen caídas", async () => {
  const m = mockFetch(async () => ({ status: 200 }));
  try {
    const d = await (await status({}, ctx, SLUGS, async () => { throw new Error("boom"); })).json();
    assert.equal(d.licenses, true);
    assert.deepEqual(d.tools, { "web-intel": false, norma43: false });
  } finally { m.restore(); }
});
