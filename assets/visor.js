/* Visor Norma 43 (Cuaderno 43): todo ocurre en el navegador, el fichero no se envía a ningún sitio. */
(function () {
  "use strict";
  var $ = function (s) { return document.querySelector(s); };
  var drop = $("[data-visor-drop]"), input = $("[data-visor-input]"), out = $("[data-visor-out]"), msg = $("[data-visor-msg]");
  if (!input || !out) return;

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function cents(s, sign) { var n = parseInt(s, 10); if (isNaN(n)) return null; return (sign === "1" ? -n : n); }
  function eur(c) { var neg = c < 0, a = Math.abs(c), i = Math.floor(a / 100), d = ("0" + (a % 100)).slice(-2); return (neg ? "-" : "") + String(i).replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + d; }
  function date(s) { if (!/^\d{6}$/.test(s)) return s; var y = parseInt(s.slice(0, 2), 10); return s.slice(4, 6) + "/" + s.slice(2, 4) + "/" + (y < 70 ? 2000 + y : 1900 + y); }
  function decode(buf) {
    var u8 = new Uint8Array(buf), s;
    try { s = new TextDecoder("utf-8", { fatal: true }).decode(u8); } catch (e) { s = new TextDecoder("windows-1252").decode(u8); }
    return s;
  }

  function parse(text) {
    var lines = text.split(/\r\n|\n|\r/).filter(function (l) { return l.trim().length; });
    var accts = [], cur = null, warnings = [];
    lines.forEach(function (l, i) {
      var t = l.slice(0, 2);
      if (t === "11") {
        cur = { bank: l.slice(2, 6), branch: l.slice(6, 10), acct: l.slice(10, 20), from: l.slice(20, 26), to: l.slice(26, 32),
          open: cents(l.slice(33, 47), l.slice(32, 33)), cur: l.slice(47, 50), name: l.slice(51, 77).trim(), mov: [], close: null, totD: 0, totH: 0, cD: null, cH: null, line: i + 1 };
        accts.push(cur);
      } else if (t === "22" && cur) {
        cur.mov.push({ op: l.slice(10, 16), val: l.slice(16, 22), com: l.slice(22, 24), own: l.slice(24, 27),
          amt: cents(l.slice(28, 42), l.slice(27, 28)), doc: l.slice(42, 52).trim(), r1: l.slice(52, 64).trim(), r2: l.slice(64, 80).trim(), concept: [] });
        var m = cur.mov[cur.mov.length - 1];
        if (m.amt === null) warnings.push("Línea " + (i + 1) + ": importe ilegible.");
        else if (m.amt < 0) cur.totD += -m.amt; else cur.totH += m.amt;
      } else if (t === "23" && cur && cur.mov.length) {
        cur.mov[cur.mov.length - 1].concept.push((l.slice(4, 42) + " " + l.slice(42, 80)).replace(/\s+/g, " ").trim());
      } else if (t === "33" && cur) {
        cur.nD = parseInt(l.slice(20, 25), 10); cur.cD = parseInt(l.slice(25, 39), 10);
        cur.nH = parseInt(l.slice(39, 44), 10); cur.cH = parseInt(l.slice(44, 58), 10);
        cur.close = cents(l.slice(59, 73), l.slice(58, 59));
      }
    });
    accts.forEach(function (a) {
      a.ok = [];
      var sum = a.mov.reduce(function (s, m) { return s + (m.amt || 0); }, 0);
      if (a.open !== null && a.close !== null) a.ok.push([a.open + sum === a.close, "Saldo inicial + movimientos = saldo final"]);
      if (a.cD !== null) a.ok.push([a.cD === a.totD && a.cH === a.totH, "Totales debe/haber del registro 33"]);
      if (a.nD !== undefined && !isNaN(a.nD)) {
        var nd = a.mov.filter(function (m) { return m.amt < 0; }).length, nh = a.mov.filter(function (m) { return m.amt > 0; }).length;
        a.ok.push([a.nD === nd && a.nH === nh, "Nº de apuntes debe/haber"]);
      }
    });
    return { accts: accts, warnings: warnings };
  }

  function render(res, name) {
    if (!res.accts.length) { show("No se reconoce como Norma 43: faltan registros 11 (cabecera de cuenta). ¿Es un CSV o un PDF?"); out.hidden = true; return; }
    show(""); var h = "";
    res.accts.forEach(function (a) {
      var iban = a.bank + " " + a.branch + " ** " + a.acct;
      var sum = a.mov.reduce(function (s, m) { return s + (m.amt || 0); }, 0);
      h += '<section class="card-flat visor-acct"><h2 class="h4">Cuenta ' + esc(iban) + (a.name ? " · " + esc(a.name) : "") + "</h2>";
      h += '<p class="muted small">' + esc(date(a.from)) + " → " + esc(date(a.to)) + " · " + a.mov.length + " movimientos</p>";
      h += '<ul class="checks">';
      h += "<li><span>Saldo inicial: <b>" + (a.open === null ? "—" : eur(a.open)) + " €</b> · Saldo final: <b>" + (a.close === null ? "—" : eur(a.close)) + " €</b> · Movimientos: <b>" + eur(sum) + " €</b></span></li>";
      a.ok.forEach(function (c) { h += "<li><span>" + (c[0] ? "✔ " : "✘ ") + esc(c[1]) + (c[0] ? "" : " — NO cuadra") + "</span></li>"; });
      h += "</ul>";
      h += '<div class="tw"><table class="uso-t"><thead><tr><th>Fecha</th><th>Valor</th><th>Concepto</th><th class="num">Importe (€)</th></tr></thead><tbody>';
      a.mov.forEach(function (m) {
        h += "<tr><td>" + esc(date(m.op)) + "</td><td>" + esc(date(m.val)) + '</td><td style="white-space:normal">' + esc(m.concept.join(" ") || [m.doc, m.r1, m.r2].join(" ").trim()) + '</td><td class="num tabnum">' + (m.amt === null ? "?" : eur(m.amt)) + "</td></tr>";
      });
      h += "</tbody></table></div></section>";
    });
    if (res.warnings.length) h += '<p class="note">' + esc(res.warnings.slice(0, 5).join(" ")) + "</p>";
    out.innerHTML = h; out.hidden = false;
  }
  function show(t) { if (!msg) return; msg.hidden = !t; var s = msg.querySelector("span"); if (s) s.textContent = t; }

  function read(file) {
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { show("El fichero pasa de 10 MB."); return; }
    var r = new FileReader();
    r.onload = function () { render(parse(decode(r.result)), file.name); };
    r.onerror = function () { show("No se pudo leer el fichero."); };
    r.readAsArrayBuffer(file);
  }
  input.addEventListener("change", function () { read(input.files && input.files[0]); });
  if (drop) {
    ["dragover", "dragenter"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); }); });
    drop.addEventListener("drop", function (e) { e.preventDefault(); read(e.dataTransfer && e.dataTransfer.files[0]); });
  }
  window.__visorN43 = { parse: parse };
})();
