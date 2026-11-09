/* Flint · Procesador por lotes en el navegador (/lote/, /en/batch/, /norma43-a-…/, /csv-a-…/).
   Misma lógica que installer/lote.py: bytes en base64 (CP850/Latin-1, firmas XAdES), detección VERI*FACTU vs Facturae,
   soporte directo de CSV bancario, vista previa instantánea en navegador y acceso directo con correo (prueba gratis u OTP). */
(function () {
  "use strict";
  var root = document.querySelector("[data-batch]");
  if (!root) return;
  var EN = document.documentElement.lang === "en";
  function T(es, en) { return EN ? en : es; }
  var KEY = "kf-mcp-license", LIC_RE = /^LIC-[A-Za-z0-9._~+\/=-]{6,1024}$/, EMAIL_RE = /^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$/;
  var EXTS = [".n43", ".c43", ".q43", ".csv", ".xml", ".xsig"], MAX_BYTES = 10 * 1024 * 1024;
  var COST = { parse_norma43: 1, validate_verifactu_xml: 3, validate_facturae: 2, bank_to_journal: 3 };
  /* Con data-batch-target (contasol | a3 | contaplus_ascii) los Norma 43 y CSV se convierten en el fichero del programa contable. */
  var TARGET = root.getAttribute("data-batch-target") || "";
  var CSV_MODE = root.getAttribute("data-batch-csv-mode") === "1";
  var bankEl = root.querySelector("[data-batch-bank]");
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
  var otpBox = null, otpInput = null, otpEmail = "";

  try {
    var fromUrl = (location.hash.match(/licencia=([^&]+)/) || location.search.match(/licencia=([^&]+)/) || [])[1];
    if (fromUrl) lic.value = decodeURIComponent(fromUrl);
    var saved = localStorage.getItem(KEY);
    if (saved && !lic.value) lic.value = saved;
  } catch (e) { /* sin almacenamiento */ }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function ext(name) { var i = name.lastIndexOf("."); return i < 0 ? "" : name.slice(i).toLowerCase(); }
  function say(text, bad) {
    msgEl.hidden = !text; msgEl.classList.toggle("bad", !!bad);
    msgEl.querySelector("span").textContent = text || "";
  }

  /* --- ficheros y vista previa instantánea --- */
  function head(bytes, max) {
    var n = Math.min(bytes.length, max || 16384), s = "";
    for (var i = 0; i < n; i++) s += String.fromCharCode(bytes[i]);
    return s;
  }
  function isVerifactu(bytes) { var h = head(bytes); return VF_TAGS.some(function (t) { return h.indexOf(t) >= 0; }); }
  function toolFor(it) {
    if (it.ext === ".csv") return ["contabridge", "bank_to_journal"];
    if (it.ext === ".n43" || it.ext === ".c43" || it.ext === ".q43") return TARGET ? ["contabridge", "bank_to_journal"] : ["norma43", "parse_norma43"];
    if (it.ext === ".xml" && isVerifactu(it.bytes)) return ["verifactu", "validate_verifactu_xml"];
    return ["verifactu", "validate_facturae"];
  }
  function previewOf(it) {
    try {
      var txt = head(it.bytes, 262144);
      var lines = txt.replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
      if (it.ext === ".n43" || it.ext === ".c43" || it.ext === ".q43") {
        var movs = lines.filter(function (l) { return l.slice(0, 2) === "22"; }).length;
        return movs ? T("Vista previa: " + movs + " mov. detectados", "Preview: " + movs + " mov. detected") : T("Listo para procesar", "Ready to process");
      }
      if (it.ext === ".csv") {
        var rows = Math.max(0, lines.filter(function (l) { return l.trim().length > 0; }).length - 1);
        return rows ? T("Vista previa: ~" + rows + " filas CSV", "Preview: ~" + rows + " CSV rows") : T("CSV listo", "CSV ready");
      }
      return T("XML listo para validar", "XML ready to validate");
    } catch (e) { return ""; }
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
      return it.file.arrayBuffer().then(function (buf) {
        it.bytes = new Uint8Array(buf);
        it.tool = toolFor(it);
        it.preview = previewOf(it);
      });
    })).then(render);
    say(skipped.length ? T("No se admiten: ", "Not supported: ") + skipped.join(", ") + T(". Solo .n43, .c43, .q43, .csv, .xml y .xsig de hasta 10 MB.", ". Only .n43, .c43, .q43, .csv, .xml and .xsig up to 10 MB.") : "", true);
  }

  var LABEL = {
    pending: T("Pendiente", "Pending"), running: T("Procesando…", "Processing…"), ok: "OK",
    warn: T("Con reparos", "With issues"), error: "Error"
  };
  var TYPE = { parse_norma43: "Norma 43", validate_verifactu_xml: "VERI*FACTU XML", validate_facturae: "Facturae 3.2.2", bank_to_journal: "Extracto → asientos" };
  function typeOf(it) {
    if (!it.tool) return "…";
    if (it.ext === ".csv") return "CSV → asientos";
    return TYPE[it.tool[1]] || "…";
  }
  function render() {
    list.hidden = !items.length;
    rowsEl.innerHTML = items.map(function (it, i) {
      var st = it.state, cls = st === "ok" ? "ok" : st === "warn" ? "warn" : st === "error" ? "bad" : "";
      var detail = it.err ? esc(it.err) : it.row ? esc(it.row.movimientos_o_facturas + " " + T("reg.", "rec.") + " · " + it.row.avisos + " " + T("avisos", "warnings")) : esc(it.preview || "");
      return "<tr><td class=\"fn\">" + esc(it.name) + "</td><td>" + typeOf(it) + "</td>" +
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

  var sampleBtns = root.querySelectorAll("[data-batch-sample]");
  sampleBtns.forEach(function (btn) {
    btn.addEventListener("click", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      var enc = new TextEncoder(), bytes, blob, file, extName;
      if (CSV_MODE) {
        var sampleCsv = "Fecha;Concepto;Importe\n2026-10-03;COBRO FACTURA 2026-104 CLIENTE DEMO SL;1250,00\n2026-10-15;RECIBO IBERDROLA CLIENTES;-42,35\n2026-10-28;COMISION MANTENIMIENTO CUENTA;-12,00\n";
        bytes = enc.encode(sampleCsv);
        blob = new Blob([bytes], { type: "text/csv" });
        file = new File([blob], "extracto_ejemplo_banco.csv", { type: "text/csv" });
        extName = ".csv";
      } else {
        var sampleN43 = "112100041802000513322610012610312000000001500009783ACME SOLUCIONES SL           \n22    0418261003261003020002000000001250000000000000000000000000                \n2301CLIENTE DEMO SL                                                             \n2303        FACTURA 2026-104                                                    \n22    0418261015261015030001000000000042350000012345000000000000                \n3321000418020005133200001000000000042350000100000000125000200000000270765978    \n88999999999999999999000006                                                      \n";
        bytes = enc.encode(sampleN43);
        blob = new Blob([bytes], { type: "text/plain" });
        file = new File([blob], "extracto_ejemplo_caixabank.n43", { type: "text/plain" });
        extName = ".n43";
      }
      if (!items.some(function (it) { return it.name === file.name; })) {
        var itemObj = { file: file, name: file.name, size: file.size, ext: extName, state: "pending", bytes: bytes };
        itemObj.tool = toolFor(itemObj);
        itemObj.preview = previewOf(itemObj);
        items.push(itemObj);
      }
      if (!lic.value) {
        try { lic.value = localStorage.getItem(KEY) || ""; } catch (e) {}
      }
      render();
      say(CSV_MODE
        ? T("Extracto CSV bancario de ejemplo cargado (3 movimientos). Escribe tu correo o licencia y pulsa Convertir.", "Sample bank CSV loaded (3 movements). Enter your email or license and click Convert.")
        : T("Extracto bancario de ejemplo cargado (2 apuntes, saldo 2.707,65 €). Escribe tu correo o licencia y pulsa Procesar.", "Sample bank statement loaded. Enter your email or license and click Process."));
    });
  });

  /* --- resolución automática correo -> licencia (prueba gratis directa o código OTP de 6 dígitos) --- */
  function ensureOtpBox() {
    if (otpBox) return;
    otpBox = document.createElement("div");
    otpBox.className = "lic";
    otpBox.hidden = true;
    otpBox.style.marginTop = "10px";
    otpBox.innerHTML = "<span class=\"lic-label\">" + T("Código de 6 dígitos (enviado a tu correo)", "6-digit code (sent to your email)") + "</span>" +
      "<span class=\"lic-field\"><input type=\"text\" inputmode=\"numeric\" autocomplete=\"one-time-code\" maxlength=\"7\" placeholder=\"123456\" data-batch-otp></span>" +
      "<span class=\"lic-help\">" + T("Introduce el código de 6 dígitos y vuelve a pulsar el botón de abajo para cargar tu licencia activa.", "Enter the 6-digit code and press the button below again to load your active license.") + "</span>";
    var parent = lic.closest(".lic") || lic.parentNode;
    parent.parentNode.insertBefore(otpBox, parent.nextSibling);
    otpInput = otpBox.querySelector("[data-batch-otp]");
  }

  async function resolveEmailLicense(email) {
    var norm = email.trim().toLowerCase();
    ensureOtpBox();
    if (!otpBox.hidden && otpEmail === norm && otpInput.value.trim()) {
      say(T("Verificando código de 6 dígitos…", "Verifying 6-digit code…"));
      var vr = await fetch("/api/otp/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email: norm, code: otpInput.value.trim() })
      });
      var vd = await vr.json().catch(function () { return {}; });
      if (!vr.ok || !vd.ok || !vd.license) {
        if (vd.expired) { otpBox.hidden = true; otpInput.value = ""; }
        say(vd.error || T("Código incorrecto. Revisa tu correo.", "Invalid code. Check your email."), true);
        if (!otpBox.hidden) otpInput.focus();
        return null;
      }
      otpBox.hidden = true;
      otpInput.value = "";
      lic.value = vd.license;
      try { localStorage.setItem(KEY, vd.license); } catch (e) {}
      return vd.license;
    }
    say(T("Activando acceso para " + norm + "…", "Activating access for " + norm + "…"));
    var tr = await fetch("/api/prueba", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: norm, lang: EN ? "en" : "es" })
    });
    var td = await tr.json().catch(function () { return {}; });
    if (tr.ok && td.ok && td.license && LIC_RE.test(td.license)) {
      lic.value = td.license;
      try { localStorage.setItem(KEY, td.license); } catch (e) {}
      return td.license;
    }
    if (tr.status === 409 || td.used) {
      var sr = await fetch("/api/otp/start", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email: norm })
      });
      var sd = await sr.json().catch(function () { return {}; });
      if (!sr.ok || !sd.ok) {
        say(sd.error || td.error || T("No pudimos enviar el código. Pega tu clave LIC-… directamente.", "Could not send code. Paste your LIC-… key directly."), true);
        return null;
      }
      otpEmail = norm;
      otpBox.hidden = false;
      otpInput.value = "";
      otpInput.focus();
      say(T("Hemos enviado un código de 6 dígitos a " + norm + " para cargar tu licencia. Escríbelo arriba y pulsa Procesar.", "We sent a 6-digit code to " + norm + " to load your license. Enter it above and click Process."));
      return null;
    }
    say(td.error || T("No se pudo activar con ese correo. Pega tu licencia LIC-….", "Could not activate with that email. Paste your LIC-… license."), true);
    return null;
  }

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
    var tool = it.tool[1], base = { fecha_proceso: nowStr(), fichero: it.name, tipo: typeOf(it) };
    if (tool === "bank_to_journal") {
      var bk = data.bank || {}, js = data.summary || {}, pend = bk.unmatched_total || 0;
      return Object.assign(base, {
        estado: js.balanced === false ? "DESCUADRADO" : (pend ? "REVISAR_555" : "OK"),
        iban_o_emisor: (bankEl && bankEl.value) || "57200001", movimientos_o_facturas: bk.movements != null ? bk.movements : (js.entries || ""),
        saldo_inicial: js.from || "", saldo_final_o_total: js.to || "",
        moneda: "EUR", avisos: pend + (data.norma43_issues || []).length, ok: js.balanced !== false && !pend
      });
    }
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
    if (!LIC_RE.test(license) && EMAIL_RE.test(license)) {
      running = true; goBtn.disabled = true;
      try {
        var resolved = await resolveEmailLicense(license);
        if (!resolved) { running = false; render(); return; }
        license = resolved;
      } catch (e) {
        running = false; render();
        say(T("Error de red al verificar el correo.", "Network error verifying email."), true);
        return;
      }
    }
    if (!LIC_RE.test(license)) {
      say(T("Escribe tu correo electrónico (para activar 25 créditos gratis o cargar tu licencia) o pega tu clave LIC-….", "Enter your email address (to get 25 free credits or load your license) or paste your LIC-… key."), true);
      lic.focus(); return;
    }
    try { localStorage.setItem(KEY, license); } catch (e) { /* sin almacenamiento */ }
    lastLicense = license; hideRefill();
    var bankAcc = bankEl ? bankEl.value.trim() : "57200001";
    if (TARGET && !/^57\d{2,10}$/.test(bankAcc)) {
      say(T("Indica la subcuenta del banco (grupo 57, p. ej. 57200001).", "Enter the bank subaccount (group 57, e.g. 57200001)."), true);
      if (bankEl) bankEl.focus(); return;
    }
    var nextEntry = 1;
    items.forEach(function (x) { if (x.data && x.data.summary && x.data.summary.entries) nextEntry += x.data.summary.entries; });
    running = true; stopFlag = false; stopBtn.disabled = false; say(""); render();
    var fatal = null, fatalCredits = false;
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      if (it.state !== "pending" && it.state !== "error") continue;
      if (stopFlag || fatal) break;
      if (!it.bytes) { it.bytes = new Uint8Array(await it.file.arrayBuffer()); it.tool = toolFor(it); it.preview = previewOf(it); }
      it.state = "running"; it.err = ""; render();
      try {
        var args = { content_base64: b64(it.bytes) };
        if (it.tool[1] === "parse_norma43") args.include_movements = true;
        if (it.tool[1] === "bank_to_journal") { args.bank_account = bankAcc || "57200001"; args.target_format = TARGET || "csv"; args.start_entry_number = nextEntry; }
        var data = await callMcp(it.tool[0], it.tool[1], args, license);
        it.data = data; it.row = summarise(it, data); it.state = it.row.ok ? "ok" : "warn";
        if (data.summary && data.summary.entries) nextEntry += data.summary.entries;
      } catch (e) {
        it.state = "error"; it.err = e.message || String(e);
        if (e.fatal) { fatal = it.err; fatalCredits = e.credits; }
      }
      render();
    }
    running = false; render();
    var ok = items.filter(function (x) { return x.row; }).length, bad = items.filter(function (x) { return x.state === "error"; }).length;
    if (fatal) {
      say(fatal + (fatalCredits
        ? T(" Recarga aquí abajo y continúa: solo se repiten los pendientes.", " Top up below and continue: only the pending files run.")
        : T(" Corrígela y vuelve a pulsar Procesar.", " Fix it and press Process again.")), true);
      if (fatalCredits) showRefill();
    }
    else if (stopFlag) say(T("Detenido. Pulsa Procesar para seguir con los pendientes.", "Stopped. Press Process to continue with the pending files."));
    else say(T(ok + " fichero(s) procesados" + (bad ? ", " + bad + " con error (no se cobran)." : ".") + " Descarga el resultado abajo.",
      ok + " file(s) processed" + (bad ? ", " + bad + " failed (not charged)." : ".") + " Download the result below."), !!bad && !ok);
  }
  /* --- recarga en 1 clic al quedarse sin créditos ---
     Mismo cálculo que el gateway (topup_pricing.py): 20 créditos por euro, bonificación desde 20 €; 10 € = 200 créditos.
     Stripe se abre en otra pestaña para no perder los ficheros de esta; si el navegador bloquea la pestaña, vamos en esta
     y Stripe devuelve a esta misma página (?recarga=cs_…). */
  var REFILL_EUR = 10, REFILL_CREDITS = 200, lastLicense = "", refillBox = null;
  var STRIPE_RE = /^https:\/\/([a-z0-9-]+\.)*(stripe\.com|link\.com)\//;
  function hideRefill() { if (refillBox) refillBox.hidden = true; }
  function showRefill() {
    if (!refillBox) {
      refillBox = document.createElement("div");
      refillBox.className = "batch-refill";
      refillBox.setAttribute("data-batch-refill", "");
      refillBox.innerHTML = '<label class="topup-waiver"><input type="checkbox" data-refill-waiver> <span>' +
        esc(T("Quiero los créditos ya. Acepto que, al empezar a usarlos, pierdo el derecho de desistimiento de 14 días sobre la parte usada.",
          "I want the credits now. I accept that once I start using them I lose the 14-day right of withdrawal on the used part.")) + '</span></label>' +
        '<button class="btn btn-primary" type="button" data-refill-go disabled></button>' +
        '<button class="btn" type="button" data-refill-continue hidden>' + esc(T("Ya he pagado: continuar lote", "I have paid: continue batch")) + '</button>' +
        '<p class="muted small">' + esc(T("Pago seguro con Stripe, IVA incluido. Se abre en otra pestaña y esta conserva tus ficheros.",
          "Secure payment with Stripe, VAT included. It opens in another tab and this one keeps your files.")) + '</p>' +
        '<p class="note bad" data-refill-err hidden><span></span></p>';
      msgEl.parentNode.insertBefore(refillBox, msgEl.nextSibling);
      var w8 = refillBox.querySelector("[data-refill-waiver]"), btn = refillBox.querySelector("[data-refill-go]");
      btn.textContent = T("Recargar " + REFILL_EUR + " € (" + REFILL_CREDITS + " créditos) con Stripe y continuar lote",
        "Top up €" + REFILL_EUR + " (" + REFILL_CREDITS + " credits) with Stripe and continue batch");
      w8.addEventListener("change", function () { btn.disabled = !w8.checked; });
      btn.addEventListener("click", refill);
      refillBox.querySelector("[data-refill-continue]").addEventListener("click", function () { if (!running) run(); });
    }
    refillBox.querySelector("[data-refill-err]").hidden = true;
    refillBox.hidden = false;
  }
  function refill() {
    var btn = refillBox.querySelector("[data-refill-go]"), err = refillBox.querySelector("[data-refill-err]");
    if (!refillBox.querySelector("[data-refill-waiver]").checked || !LIC_RE.test(lastLicense)) return;
    var tab = null;
    try { tab = window.open("", "_blank"); } catch (e) { tab = null; } /* se abre en el clic: si no, el bloqueador la frena */
    err.hidden = true; btn.disabled = true; btn.setAttribute("aria-busy", "true");
    fetch("/api/recarga", { method: "POST", headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ license: lastLicense, amount: REFILL_EUR, currency: "eur", waiver: true, lang: EN ? "en" : "es", return_path: location.pathname }) })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.ok || !STRIPE_RE.test(d.url || "")) throw new Error(d.error || T("No se pudo iniciar el pago.", "Could not start the payment."));
        if (tab && !tab.closed) {
          try { tab.opener = null; } catch (e) { /* ignorar */ }
          tab.location.href = d.url;
          btn.removeAttribute("aria-busy"); btn.disabled = false;
          refillBox.querySelector("[data-refill-continue]").hidden = false;
          say(T("Completa el pago en la pestaña de Stripe y pulsa «Ya he pagado: continuar lote».", "Finish the payment in the Stripe tab and press “I have paid: continue batch”."));
        } else location.href = d.url;
      })
      .catch(function (e) {
        if (tab && !tab.closed) tab.close();
        err.querySelector("span").textContent = e.message || T("No se pudo iniciar el pago.", "Could not start the payment.");
        err.hidden = false; btn.removeAttribute("aria-busy"); btn.disabled = false;
      });
  }
  /* vuelta de Stripe a esta página: ?recarga=cs_… */
  (function () {
    var sid = new URLSearchParams(location.search).get("recarga") || "";
    if (!/^cs_[A-Za-z0-9_]{10,250}$/.test(sid)) return;
    try { history.replaceState(null, "", location.pathname + location.hash); } catch (e) { /* ignorar */ }
    var tries = 0, nf = new Intl.NumberFormat(EN ? "en-GB" : "es-ES");
    say(T("Pago recibido. Sumando los créditos a tu licencia…", "Payment received. Adding the credits to your license…"));
    (function poll() {
      fetch("/api/recarga?session=" + encodeURIComponent(sid), { headers: { accept: "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.ok && d.status === "applied") {
            say(T("Recarga completada: +" + nf.format(d.credits) + " créditos (saldo: " + nf.format(d.balance) + "). Vuelve a la pestaña del lote y pulsa «Ya he pagado: continuar lote», o suelta aquí los ficheros pendientes y pulsa Procesar.",
              "Top-up complete: +" + nf.format(d.credits) + " credits (balance: " + nf.format(d.balance) + "). Go back to the batch tab and press “I have paid: continue batch”, or drop the pending files here and press Process."));
            return;
          }
          if (++tries < 15) setTimeout(poll, 2000);
          else say(T("El pago está hecho; los créditos pueden tardar un minuto. Mira tu saldo en Mi saldo.", "The payment went through; the credits may take a minute. Check My balance."));
        })
        .catch(function () { if (++tries < 15) setTimeout(poll, 2000); });
    })();
  })();

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
    return "\uFEFF" + out.join("\r\n") + "\r\n";
  }
  function save(name, content, type) {
    var blob = content instanceof Blob ? content : new Blob([content], { type: type + ";charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
  }
  var CSV_NAME = EN ? "flint-summary.csv" : "resumen-flint.csv";
  function unb64(s) { var b = atob(s), u = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u; }
  function targetFiles() {
    var seen = {};
    return items.filter(function (it) { return it.row && it.data && it.data.content_base64; }).map(function (it) {
      var fn = it.data.filename || "importar.txt", dot = fn.lastIndexOf("."), stem = it.name.replace(/\.[^.]+$/, "");
      var n = fn.slice(0, dot) + "-" + stem + fn.slice(dot); seen[n] = (seen[n] || 0) + 1;
      return { name: seen[n] > 1 ? seen[n] + "-" + n : n, orig: fn, bytes: unb64(it.data.content_base64) };
    });
  }
  csvBtn.addEventListener("click", function () {
    if (!TARGET) { save(CSV_NAME, csvText(), "text/csv"); return; }
    var fs = targetFiles();
    if (!fs.length) return;
    if (fs.length === 1) save(fs[0].orig, new Blob([fs[0].bytes], { type: "application/octet-stream" }));
    else save(TARGET + "-" + new Date().toISOString().slice(0, 10) + ".zip", zip(fs));
  });

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
      var name = enc.encode(f.name), data = f.bytes || enc.encode(f.text), crc = crc32(data);
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
    var files = [{ name: CSV_NAME, text: csvText() }].concat(TARGET ? targetFiles() : [], done.map(function (it) {
      var n = it.name + ".flint.json"; seen[n] = (seen[n] || 0) + 1;
      return { name: seen[n] > 1 ? it.name + "." + seen[n] + ".flint.json" : n, text: jsonText(it) };
    }));
    save("flint-lote-" + new Date().toISOString().slice(0, 10) + ".zip", zip(files));
  });

  render();
})();
