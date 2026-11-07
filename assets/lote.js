/* Flint · Procesador por lotes en el navegador (/lote/ y /en/batch/).
   Misma lógica que installer/lote.py: bytes en base64 (CP850/Latin-1, firmas XAdES), detección VERI*FACTU vs Facturae,
   resumen CSV para Excel y un .flint.json por fichero. Llama a /<slug>/mcp del mismo origen con la licencia del usuario. */
(function () {
  "use strict";
  var root = document.querySelector("[data-batch]");
  if (!root) return;
  var EN = document.documentElement.lang === "en";
  function T(es, en) { return EN ? en : es; }
  var KEY = "kf-mcp-license", LIC_RE = /^LIC-[A-Za-z0-9._~+\/=-]{6,1024}$/;
  var EXTS = [".n43", ".c43", ".q43", ".xml", ".xsig"], MAX_BYTES = 10 * 1024 * 1024;
  var COST = { parse_norma43: 1, validate_verifactu_xml: 3, validate_facturae: 2 };
  var VF_TAGS = ["RegFactuSistemaFacturacion", "RegistroAlta", "RegistroAnulacion", "SuministroLR"];
  var SEP = EN ? "," : ";";
  var FIELDS = ["fecha_proceso", "fichero", "tipo", "estado", "iban_o_emisor", "movimientos_o_facturas",
    "saldo_inicial", "saldo_final_o_total", "moneda", "avisos"];
  var HEAD_EN = ["processed_at", "file", "type", "status", "iban_or_issuer", "movements_or_invoices",
    "opening_balance", "closing_balance_or_total", "currency", "warnings"];

  var form = root.querySelector("[data-batch-form]"), lic = root.querySelector("[data-batch-lic]");
  var drop = root.querySelector("[data-batch-drop]"), input = root.querySelector("[data-batch-input]");
  var list = root.querySelector("[data-batch-list]"), rowsEl = root.querySelector("[data-batch-rows]");
  var goBtn = root.querySelector("[data-batch-go]"), stopBtn = root.querySelector("[data-batch-stop]");
  var clearBtn = root.querySelector("[data-batch-clear]"), costEl = root.querySelector("[data-batch-cost]");
  var outEl = root.querySelector("[data-batch-out]"), msgEl = root.querySelector("[data-batch-msg]");
  var csvBtn = root.querySelector("[data-batch-csv]"), zipBtn = root.querySelector("[data-batch-zip]");

  var items = [], running = false, stopFlag = false;

  try { var saved = localStorage.getItem(KEY); if (saved && !lic.value) lic.value = saved; } catch (e) { /* sin almacenamiento */ }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function ext(name) { var i = name.lastIndexOf("."); return i < 0 ? "" : name.slice(i).toLowerCase(); }
  function say(text, bad) {
    msgEl.hidden = !text; msgEl.classList.toggle("bad", !!bad);
    msgEl.querySelector("span").textContent = text || "";
  }

  /* --- ficheros --- */
  function head(bytes) {
    var n = Math.min(bytes.length, 16384), s = "";
    for (var i = 0; i < n; i++) s += String.fromCharCode(bytes[i]);
    return s;
  }
  function isVerifactu(bytes) { var h = head(bytes); return VF_TAGS.some(function (t) { return h.indexOf(t) >= 0; }); }
  function toolFor(it) {
    if (it.ext === ".n43" || it.ext === ".c43" || it.ext === ".q43") return ["norma43", "parse_norma43"];
    if (it.ext === ".xml" && isVerifactu(it.bytes)) return ["verifactu", "validate_verifactu_xml"];
    return ["verifactu", "validate_facturae"];
  }
  function b64(bytes) {
    var s = "", C = 0x8000;
    for (var i = 0; i < bytes.length; i += C) s += String.fromCharCode.apply(null, bytes.subarray(i, i + C));
    return btoa(s);
  }
  function addFiles(files) {
    var skipped = [];
    Array.prototype.forEach.call(files, function (f) {
      var x = ext(f.name);
      if (EXTS.indexOf(x) < 0) { skipped.push(f.name); return; }
      if (f.size > MAX_BYTES) { skipped.push(f.name + " (> 10 MB)"); return; }
      if (items.some(function (it) { return it.name === f.name && it.size === f.size; })) return;
      items.push({ file: f, name: f.name, size: f.size, ext: x, state: "pending" });
    });
    Promise.all(items.filter(function (it) { return !it.bytes; }).map(function (it) {
      return it.file.arrayBuffer().then(function (buf) { it.bytes = new Uint8Array(buf); it.tool = toolFor(it); });
    })).then(render);
    say(skipped.length ? T("No se admiten: ", "Not supported: ") + skipped.join(", ") + T(". Solo .n43, .c43, .q43, .xml y .xsig de hasta 10 MB.", ". Only .n43, .c43, .q43, .xml and .xsig up to 10 MB.") : "", true);
  }

  var LABEL = {
    pending: T("Pendiente", "Pending"), running: T("Procesando…", "Processing…"), ok: "OK",
    warn: T("Con reparos", "With issues"), error: "Error"
  };
  var TYPE = { parse_norma43: "Norma 43", validate_verifactu_xml: "VERI*FACTU XML", validate_facturae: "Facturae 3.2.2" };
  function render() {
    list.hidden = !items.length;
    rowsEl.innerHTML = items.map(function (it, i) {
      var st = it.state, cls = st === "ok" ? "ok" : st === "warn" ? "warn" : st === "error" ? "bad" : "";
      var detail = it.err ? esc(it.err) : it.row ? esc(it.row.movimientos_o_facturas + " " + T("reg.", "rec.") + " · " + it.row.avisos + " " + T("avisos", "warnings")) : "";
      return "<tr><td class=\"fn\">" + esc(it.name) + "</td><td>" + (it.tool ? TYPE[it.tool[1]] : "…") + "</td>" +
        "<td><span class=\"status " + cls + "\">" + LABEL[st] + "</span></td><td class=\"muted small\">" + detail + "</td>" +
        "<td class=\"num\">" + (it.row ? "<button type=\"button\" class=\"btn btn-quiet btn-sm\" data-json=\"" + i + "\">.flint.json</button>" :
          (!running && st !== "running" ? "<button type=\"button\" class=\"btn btn-quiet btn-sm\" data-remove=\"" + i + "\" aria-label=\"" + T("Quitar ", "Remove ") + esc(it.name) + "\">×</button>" : "")) + "</td></tr>";
    }).join("");
    var todo = items.filter(function (it) { return it.state === "pending" || it.state === "error"; });
    var credits = todo.reduce(function (a, it) { return a + (it.tool ? COST[it.tool[1]] : 0); }, 0);
    costEl.textContent = todo.length ? T(todo.length + " fichero(s) · ≈ " + credits + " créditos", todo.length + " file(s) · ≈ " + credits + " credits") : "";
    goBtn.disabled = running || !todo.length;
    goBtn.querySelector("span").textContent = todo.length ? T("Procesar " + todo.length + " fichero(s)", "Process " + todo.length + " file(s)") : T("Procesar", "Process");
    stopBtn.hidden = !running;
    clearBtn.hidden = running || !items.length;
    var done = items.filter(function (it) { return it.row; });
    outEl.hidden = !done.length;
  }

  rowsEl.addEventListener("click", function (ev) {
    var r = ev.target.closest("[data-remove]"), j = ev.target.closest("[data-json]");
    if (r && !running) { items.splice(+r.getAttribute("data-remove"), 1); render(); }
    if (j) { var it = items[+j.getAttribute("data-json")]; save(it.name + ".flint.json", jsonText(it), "application/json"); }
  });
  input.addEventListener("change", function () { addFiles(input.files); input.value = ""; });
  ["dragenter", "dragover"].forEach(function (t) {
    drop.addEventListener(t, function (ev) { ev.preventDefault(); drop.classList.add("over"); });
  });
  ["dragleave", "drop"].forEach(function (t) {
    drop.addEventListener(t, function (ev) { ev.preventDefault(); drop.classList.remove("over"); });
  });
  drop.addEventListener("drop", function (ev) { if (ev.dataTransfer && ev.dataTransfer.files) addFiles(ev.dataTransfer.files); });
  /* soltar fuera de la zona no debe abrir el fichero en la pestaña */
  window.addEventListener("dragover", function (ev) { ev.preventDefault(); });
  window.addEventListener("drop", function (ev) { ev.preventDefault(); });
  clearBtn.addEventListener("click", function () { items = []; say(""); render(); });
  stopBtn.addEventListener("click", function () { stopFlag = true; stopBtn.disabled = true; });

  /* --- llamada MCP (Streamable HTTP sin sesión, igual que lote.py) --- */
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function parseBody(text) {
    var t = text.trim();
    if (t.charAt(0) === "{") return JSON.parse(t);
    var data = t.split(/\r?\n/).filter(function (l) { return l.indexOf("data:") === 0; }).map(function (l) { return l.slice(5).trim(); });
    for (var i = data.length - 1; i >= 0; i--) {
      try { var m = JSON.parse(data[i]); if (m && (m.result || m.error)) return m; } catch (e) { /* siguiente */ }
    }
    throw new Error(T("Respuesta del servidor no reconocida.", "Unrecognised server response."));
  }
  function Fatal(msg, credits) { this.message = msg; this.fatal = true; this.credits = !!credits; }
  async function callMcp(slug, tool, args, license) {
    var body = JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: tool, arguments: args } });
    var last;
    for (var attempt = 0; attempt < 3; attempt++) {
      var res;
      try {
        res = await fetch("/" + slug + "/mcp", {
          method: "POST", credentials: "omit",
          headers: { "content-type": "application/json", accept: "application/json, text/event-stream", authorization: "Bearer " + license },
          body: body
        });
      } catch (e) {
        last = new Error(T("Error de red. Revisa la conexión.", "Network error. Check your connection."));
        if (attempt < 2) { await sleep(2000 * (attempt + 1)); continue; }
        throw last;
      }
      var text = await res.text();
      if (res.status === 401 || res.status === 403) throw new Fatal(T("La licencia no es válida. Cópiala de nuevo desde el correo.", "The license is not valid. Copy it again from the email."));
      if ([429, 502, 503, 504].indexOf(res.status) >= 0 && attempt < 2) {
        last = new Error("HTTP " + res.status); await sleep((res.status === 429 ? 8000 : 2000) * (attempt + 1)); continue;
      }
      var msg;
      try { msg = parseBody(text); } catch (e) { throw new Error("HTTP " + res.status + ": " + text.slice(0, 200)); }
      if (msg.error) {
        var em = String(msg.error.message || JSON.stringify(msg.error));
        if (/cr[eé]dito|credit|saldo|balance|quota/i.test(em)) throw new Fatal(em, true);
        throw new Error(em);
      }
      var r = msg.result || {};
      if (r.isError) {
        var txt = (r.content || []).map(function (c) { return c.text || ""; }).join(" ").trim();
        if (/cr[eé]ditos? insuficientes|sin cr[eé]ditos|insufficient credits|out of credits|402/i.test(txt)) throw new Fatal(txt, true);
        throw new Error(txt || T("La herramienta devolvió un error (no se cobra).", "The tool returned an error (not charged)."));
      }
      var data = r.structuredContent;
      if (data && typeof data === "object" && Object.keys(data).length === 1 && "result" in data) data = data.result;
      if (!data && r.content && r.content[0] && r.content[0].text) data = JSON.parse(r.content[0].text);
      return data && typeof data === "object" ? data : { result: data };
    }
    throw last || new Error(T("Sin respuesta del servidor.", "No response from the server."));
  }

  /* --- datos leídos del propio XML (nunca inventados) --- */
  function xmlDoc(bytes) {
    try {
      var h = head(bytes), m = /encoding=["']([A-Za-z0-9_-]+)/.exec(h);
      var txt = new TextDecoder((m && m[1]) || "utf-8", { fatal: false }).decode(bytes);
      var d = new DOMParser().parseFromString(txt, "application/xml");
      return d.getElementsByTagName("parsererror").length ? null : d;
    } catch (e) { return null; }
  }
  function first(node, path) {
    var cur = node;
    for (var i = 0; i < path.length && cur; i++) cur = cur.getElementsByTagNameNS("*", path[i])[0];
    return cur ? cur.textContent.trim() : "";
  }
  function issuesOf(d) { return (d.issues || d.errors || []).length || (typeof d.errors === "number" ? d.errors : 0); }
  function nowStr() {
    var d = new Date(), p = function (n) { return (n < 10 ? "0" : "") + n; };
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + " " + p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());
  }

  function summarise(it, data) {
    var tool = it.tool[1], base = { fecha_proceso: nowStr(), fichero: it.name, tipo: TYPE[tool] };
    if (tool === "parse_norma43") {
      var acc = (data.accounts || [])[0] || {}, sm = data.summary || {}, valid = data.valid !== false;
      return Object.assign(base, {
        estado: valid ? "OK" : "CON_ERRORES",
        iban_o_emisor: acc.iban_formatted || acc.iban || acc.ccc || "",
        movimientos_o_facturas: sm.movements != null ? sm.movements : (acc.movements || []).length,
        saldo_inicial: acc.opening_balance != null ? acc.opening_balance : "",
        saldo_final_o_total: acc.closing_balance != null ? acc.closing_balance : "",
        moneda: acc.currency || "EUR", avisos: (data.issues || []).length, ok: valid
      });
    }
    var doc = xmlDoc(it.bytes);
    if (tool === "validate_verifactu_xml") {
      var v = !!data.valid;
      return Object.assign(base, {
        estado: v ? "OK" : "CADENA_CON_ERRORES",
        iban_o_emisor: doc ? first(doc, ["IDEmisorFactura"]) || first(doc, ["IDEmisorFacturaAnulada"]) : "",
        movimientos_o_facturas: typeof data.records === "number" ? data.records : "",
        saldo_inicial: "", saldo_final_o_total: String(data.last_huella || "").slice(0, 16),
        moneda: "EUR", avisos: issuesOf(data), ok: v
      });
    }
    var fv = !!data.valid;
    return Object.assign(base, {
      estado: fv ? "OK" : "CON_REPAROS",
      iban_o_emisor: doc ? first(doc, ["SellerParty", "TaxIdentificationNumber"]) : "",
      movimientos_o_facturas: typeof data.invoices === "number" ? data.invoices : 1,
      saldo_inicial: data.signed ? "FIRMADA" : "SIN_FIRMA",
      saldo_final_o_total: doc ? first(doc, ["Batch", "TotalInvoicesAmount", "TotalAmount"]) || first(doc, ["InvoiceTotals", "InvoiceTotal"]) : "",
      moneda: doc ? first(doc, ["Batch", "InvoiceCurrencyCode"]) || "EUR" : "EUR", avisos: issuesOf(data), ok: fv
    });
  }

  async function run() {
    var license = lic.value.trim().replace(/^["']|["']$/g, "");
    if (!LIC_RE.test(license)) {
      say(T("Pega una licencia válida (empieza por LIC-).", "Paste a valid license (starts with LIC-)."), true);
      lic.focus(); return;
    }
    try { localStorage.setItem(KEY, license); } catch (e) { /* sin almacenamiento */ }
    running = true; stopFlag = false; stopBtn.disabled = false; say(""); render();
    var fatal = null, fatalCredits = false;
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      if (it.state !== "pending" && it.state !== "error") continue;
      if (stopFlag || fatal) break;
      if (!it.bytes) { it.bytes = new Uint8Array(await it.file.arrayBuffer()); it.tool = toolFor(it); }
      it.state = "running"; it.err = ""; render();
      try {
        var args = { content_base64: b64(it.bytes) };
        if (it.tool[1] === "parse_norma43") args.include_movements = true;
        var data = await callMcp(it.tool[0], it.tool[1], args, license);
        it.data = data; it.row = summarise(it, data); it.state = it.row.ok ? "ok" : "warn";
      } catch (e) {
        it.state = "error"; it.err = e.message || String(e);
        if (e.fatal) { fatal = it.err; fatalCredits = e.credits; }
      }
      render();
    }
    running = false; render();
    var ok = items.filter(function (x) { return x.row; }).length, bad = items.filter(function (x) { return x.state === "error"; }).length;
    if (fatal) say(fatal + (fatalCredits
      ? T(" Recarga en Mi saldo y vuelve a pulsar Procesar: solo se repiten los pendientes.", " Top up under My balance and press Process again: only the pending files run.")
      : T(" Corrígela y vuelve a pulsar Procesar.", " Fix it and press Process again.")), true);
    else if (stopFlag) say(T("Detenido. Pulsa Procesar para seguir con los pendientes.", "Stopped. Press Process to continue with the pending files."));
    else say(T(ok + " fichero(s) procesados" + (bad ? ", " + bad + " con error (no se cobran)." : ".") + " Descarga el resumen abajo.",
      ok + " file(s) processed" + (bad ? ", " + bad + " failed (not charged)." : ".") + " Download the summary below."), !!bad && !ok);
  }
  form.addEventListener("submit", function (ev) { ev.preventDefault(); if (!running) run(); });

  /* --- salidas --- */
  function jsonText(it) { return JSON.stringify(it.data, null, 2); }
  var NUM = { saldo_inicial: 1, saldo_final_o_total: 1 };
  function cell(k, v) {
    var s = v == null ? "" : String(v);
    if (NUM[k] && /^-?\d+(\.\d+)?$/.test(s)) { if (!EN) s = s.replace(".", ","); }
    else if (/^[=+\-@\t\r]/.test(s)) s = "'" + s; /* evita fórmulas en Excel */
    return /["\n\r]/.test(s) || s.indexOf(SEP) >= 0 ? '"' + s.replace(/"/g, '""') + '"' : s;
  }
  function csvText() {
    var rows = items.filter(function (it) { return it.row; });
    var out = [(EN ? HEAD_EN : FIELDS).join(SEP)].concat(rows.map(function (it) {
      return FIELDS.map(function (k) { return cell(k, it.row[k]); }).join(SEP);
    }));
    return "﻿" + out.join("\r\n") + "\r\n";
  }
  function save(name, content, type) {
    var blob = content instanceof Blob ? content : new Blob([content], { type: type + ";charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
  }
  var CSV_NAME = EN ? "flint-summary.csv" : "resumen-flint.csv";
  csvBtn.addEventListener("click", function () { save(CSV_NAME, csvText(), "text/csv"); });

  /* ZIP sin compresión (método 0): resumen + un .flint.json por fichero, sin librerías externas. */
  var CRC = (function () {
    var t = new Uint32Array(256);
    for (var n = 0; n < 256; n++) { var c = n; for (var k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; }
    return t;
  })();
  function crc32(b) { var c = 0xFFFFFFFF; for (var i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  function zip(files) {
    var enc = new TextEncoder(), parts = [], central = [], offset = 0, d = new Date();
    var time = (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1);
    var date = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
    files.forEach(function (f) {
      var name = enc.encode(f.name), data = enc.encode(f.text), crc = crc32(data);
      var lh = new DataView(new ArrayBuffer(30));
      lh.setUint32(0, 0x04034b50, true); lh.setUint16(4, 20, true); lh.setUint16(6, 0x0800, true); lh.setUint16(8, 0, true);
      lh.setUint16(10, time, true); lh.setUint16(12, date, true); lh.setUint32(14, crc, true);
      lh.setUint32(18, data.length, true); lh.setUint32(22, data.length, true); lh.setUint16(26, name.length, true); lh.setUint16(28, 0, true);
      parts.push(lh.buffer, name, data);
      var ch = new DataView(new ArrayBuffer(46));
      ch.setUint32(0, 0x02014b50, true); ch.setUint16(4, 20, true); ch.setUint16(6, 20, true); ch.setUint16(8, 0x0800, true);
      ch.setUint16(10, 0, true); ch.setUint16(12, time, true); ch.setUint16(14, date, true); ch.setUint32(16, crc, true);
      ch.setUint32(20, data.length, true); ch.setUint32(24, data.length, true); ch.setUint16(28, name.length, true);
      ch.setUint32(42, offset, true);
      central.push(ch.buffer, name);
      offset += 30 + name.length + data.length;
    });
    var size = central.reduce(function (a, p) { return a + p.byteLength; }, 0);
    var end = new DataView(new ArrayBuffer(22));
    end.setUint32(0, 0x06054b50, true); end.setUint16(8, files.length, true); end.setUint16(10, files.length, true);
    end.setUint32(12, size, true); end.setUint32(16, offset, true);
    return new Blob(parts.concat(central, [end.buffer]), { type: "application/zip" });
  }
  zipBtn.addEventListener("click", function () {
    var done = items.filter(function (it) { return it.row; }), seen = {};
    var files = [{ name: CSV_NAME, text: csvText() }].concat(done.map(function (it) {
      var n = it.name + ".flint.json"; seen[n] = (seen[n] || 0) + 1;
      return { name: seen[n] > 1 ? it.name + "." + seen[n] + ".flint.json" : n, text: jsonText(it) };
    }));
    save("flint-lote-" + new Date().toISOString().slice(0, 10) + ".zip", zip(files));
  });

  render();
})();
