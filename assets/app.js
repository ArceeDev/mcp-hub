/* KeyFlint MCP: copiar, pestañas, selector de servidor, licencia en vivo y enlaces de 1 clic. */
(function () {
  "use strict";
  var PH = "LIC-tu-licencia", KEY = "kf-mcp-license", SAFE = /^[A-Za-z0-9._~+\/=-]{6,1024}$/;
  var CHECK = '<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>';

  function store(k, v) {
    try {
      if (v === undefined) return localStorage.getItem(k);
      if (v) localStorage.setItem(k, v); else localStorage.removeItem(k);
    } catch (e) { return null; }
    return null;
  }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  /* copiar */
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-copy]"); if (!b) return;
    var el = document.getElementById(b.getAttribute("data-copy")); if (!el) return;
    var text = el.innerText.replace(/ /g, " ");
    function done() {
      var label = b.querySelector("span"), old = label ? label.textContent : null;
      b.classList.add("done"); if (label) label.textContent = "Copiado";
      setTimeout(function () { b.classList.remove("done"); if (label) label.textContent = old; }, 1600);
    }
    function fallback() {
      var r = document.createRange(); r.selectNodeContents(el);
      var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
      try { document.execCommand("copy"); done(); } catch (e) { /* el texto queda seleccionado */ }
      s.removeAllRanges();
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, fallback); else fallback();
  });

  /* pestañas accesibles (flechas, Inicio, Fin) */
  function selectTab(list, tab, focus, remember) {
    $$('[role="tab"]', list).forEach(function (t) {
      var on = t === tab;
      t.setAttribute("aria-selected", on ? "true" : "false"); t.tabIndex = on ? 0 : -1;
      var p = document.getElementById(t.getAttribute("aria-controls"));
      if (p) { if (on) p.removeAttribute("data-hidden"); else p.setAttribute("data-hidden", ""); }
    });
    if (focus) tab.focus();
    if (remember) store("kf-mcp-client", tab.getAttribute("data-client"));
  }
  $$('[role="tablist"]').forEach(function (list) {
    var tabs = $$('[role="tab"]', list);
    list.addEventListener("click", function (ev) { var t = ev.target.closest('[role="tab"]'); if (t) selectTab(list, t, false, true); });
    list.addEventListener("keydown", function (ev) {
      var i = tabs.indexOf(document.activeElement); if (i < 0) return;
      var n = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[ev.key];
      if (n === undefined) return;
      ev.preventDefault();
      selectTab(list, tabs[(n + tabs.length) % tabs.length], true, true);
    });
    var saved = store("kf-mcp-client");
    var t = saved && list.querySelector('[data-client="' + saved + '"]');
    if (t) selectTab(list, t, false, false);
  });

  /* selector de servidor (portada) */
  $$("[data-pick]").forEach(function (b) {
    b.addEventListener("click", function () {
      var slug = b.getAttribute("data-pick");
      $$("[data-pick]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      $$("[data-pick-panel]").forEach(function (p) {
        if (p.getAttribute("data-pick-panel") === slug) p.removeAttribute("data-hidden"); else p.setAttribute("data-hidden", "");
      });
    });
  });

  /* licencia en vivo + enlaces de 1 clic */
  var installers = $$("[data-installer]");
  installers.forEach(function (ins) {
    $$("pre", ins).forEach(function (pre) { pre.setAttribute("data-tpl", pre.textContent); });
  });
  function b64(s) { return btoa(unescape(encodeURIComponent(s))); }
  function apply(lic) {
    var ok = !!lic && SAFE.test(lic), value = ok ? lic : PH;
    installers.forEach(function (ins) {
      var cfg = JSON.parse(ins.getAttribute("data-installer"));
      if (cfg.server && cfg.server.env) cfg.server.env.KEYFLINT_LICENSE = value;
      $$("pre", ins).forEach(function (pre) {
        pre.firstChild.textContent = pre.getAttribute("data-tpl").split(PH).join(value);
      });
      var c = cfg.server && ins.querySelector('[data-deeplink="cursor"]');
      if (c) c.href = "cursor://anysphere.cursor-deeplink/mcp/install?name=" + encodeURIComponent(cfg.slug) +
        "&config=" + encodeURIComponent(b64(JSON.stringify(cfg.server)));
      var v = cfg.server && ins.querySelector('[data-deeplink="vscode"]');
      if (v) v.href = "vscode:mcp/install?" + encodeURIComponent(JSON.stringify(cfg.server.url ?
        { name: cfg.slug, type: "http", url: cfg.server.url } :
        { name: cfg.slug, type: "stdio", command: cfg.server.command, args: cfg.server.args, env: cfg.server.env }));
      var input = ins.querySelector("[data-license]"), state = ins.querySelector("[data-license-state]"), help = ins.querySelector(".lic-help");
      if (input && document.activeElement !== input) input.value = lic || "";
      if (state) state.innerHTML = ok ? CHECK : "";
      if (help) {
        var bad = !!lic && !ok;
        help.classList.toggle("warn", bad);
        help.textContent = bad ? "Esa licencia tiene caracteres no válidos. Cópiala de nuevo desde el correo." :
          ok ? "Licencia aplicada en todos los fragmentos y botones." : "Se rellena en todos los fragmentos. No sale de tu navegador.";
      }
    });
  }
  document.addEventListener("input", function (ev) {
    if (!ev.target.matches("[data-license]")) return;
    var lic = ev.target.value.trim();
    store(KEY, SAFE.test(lic) ? lic : "");
    apply(lic);
  });
  apply(store(KEY) || "");

  /* saldo */
  var bf = document.querySelector("[data-balance-form]");
  if (bf) {
    var out = document.querySelector("[data-balance-out]"), err = document.querySelector("[data-balance-err]");
    var nf = new Intl.NumberFormat("es-ES");
    var TIERS = { community: "Gratis", pro: "Pro", indie: "Indie", agency: "Agency", studio: "Studio", lifetime: "Founder" };
    var STATUS = { active: "Activa", grace_period: "En periodo de gracia", expired: "Caducada", suspended: "Suspendida", revoked: "Revocada" };
    if (!bf.license.value) bf.license.value = store(KEY) || "";
    function f(name, v) { var el = out.querySelector('[data-f="' + name + '"]'); if (el) el.textContent = v; }
    bf.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var lic = bf.license.value.trim(), btn = bf.querySelector("button");
      out.hidden = true; err.hidden = true;
      if (!SAFE.test(lic)) { err.querySelector("span").textContent = "Pega la licencia completa, tal como aparece en el correo."; err.hidden = false; return; }
      btn.disabled = true; btn.setAttribute("aria-busy", "true");
      fetch("/api/saldo?license=" + encodeURIComponent(lic), { headers: { accept: "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.ok) throw new Error(d.error || "No se pudo consultar el saldo.");
          f("tier", "Plan " + (TIERS[d.tier] || d.tier)); f("status", STATUS[d.status] || d.status);
          out.querySelector('[data-f="status"]').className = "status" + (d.status === "active" ? " ok" : " warn");
          f("balance", nf.format(d.balance)); f("consumed", nf.format(d.consumed)); f("allowance", nf.format(d.allowance));
          var m = out.querySelector("[data-meter]"), pct = d.allowance ? Math.max(0, Math.min(100, d.balance / d.allowance * 100)) : 0;
          m.setAttribute("aria-valuemax", d.allowance); m.setAttribute("aria-valuenow", d.balance);
          m.setAttribute("aria-label", nf.format(d.balance) + " de " + nf.format(d.allowance) + " créditos");
          m.firstElementChild.style.width = pct + "%"; m.classList.toggle("low", pct < 15);
          out.hidden = false;
          store(KEY, lic);
          topupLicense = d.status === "active" || d.status === "grace_period" ? lic : "";
          syncTopup();
          loadUsage(lic);
        })
        .catch(function (e) { err.querySelector("span").textContent = e.message || "No se pudo consultar el saldo."; err.hidden = false; })
        .then(function () { btn.disabled = false; btn.removeAttribute("aria-busy"); });
    });
  }

  /* recarga libre: mismo cálculo que el gateway (topup_pricing.py); el gateway manda al cobrar */
  var topupLicense = "";
  var tb = document.querySelector("[data-topup]");
  function syncTopup() {}
  if (tb) {
    var cfg = JSON.parse(tb.getAttribute("data-topup"));
    var rng = tb.querySelector("[data-topup-range]"), amt = tb.querySelector("[data-topup-amount]");
    var waiver = tb.querySelector("[data-topup-waiver]"), go = tb.querySelector("[data-topup-go]"), terr = tb.querySelector("[data-topup-err]");
    var nfT = new Intl.NumberFormat("es-ES");
    function bonusOf(eur) { var b = 0; cfg.tiers.forEach(function (t) { if (eur >= t[0]) b = t[1]; }); return b; }
    function creditsOf(eur) { return eur < cfg.min ? 0 : Math.floor(eur * 100 * cfg.rate * (100 + bonusOf(eur)) / 10000); }
    function valid(eur) { return Number.isInteger(eur) && eur >= cfg.min && eur <= cfg.max; }
    syncTopup = function () {
      var eur = Number(amt.value), ok = valid(eur), b = bonusOf(eur), c = creditsOf(eur);
      tb.querySelector("[data-topup-credits]").textContent = ok ? nfT.format(c) : "—";
      var bonus = tb.querySelector("[data-topup-bonus]"); bonus.hidden = !ok || !b; bonus.textContent = "+" + b + " %";
      tb.querySelector("[data-topup-eq]").textContent = ok ? "≈ " + nfT.format(Math.floor(c / 4)) + " extractos Norma 43 leídos y conciliados" : "Entre " + cfg.min + " € y " + cfg.max + " €, sin decimales";
      var next = cfg.tiers.filter(function (t) { return t[0] > eur; })[0];
      tb.querySelector("[data-topup-next]").textContent = ok && next
        ? "Con " + next[0] + " € (" + (next[0] - eur) + " € más) recibes " + nfT.format(creditsOf(next[0])) + " créditos: +" + next[1] + " %." : "";
      tb.querySelectorAll("[data-tier-min]").forEach(function (li) {
        var m = Number(li.getAttribute("data-tier-min")), nx = cfg.tiers.filter(function (t) { return t[0] > m; })[0];
        li.classList.toggle("on", ok && eur >= m && (!nx || eur < nx[0]));
      });
      tb.querySelector("[data-topup-label]").textContent = ok ? "Recargar " + eur + " €" : "Recargar";
      go.disabled = !(ok && waiver.checked && topupLicense);
    };
    rng.addEventListener("input", function () { amt.value = rng.value; syncTopup(); });
    amt.addEventListener("input", function () { var v = Number(amt.value); if (v >= cfg.min && v <= Number(rng.max)) rng.value = v; syncTopup(); });
    waiver.addEventListener("change", syncTopup);
    go.addEventListener("click", function () {
      var eur = Number(amt.value);
      if (!valid(eur) || !waiver.checked || !topupLicense) return;
      terr.hidden = true; go.disabled = true; go.setAttribute("aria-busy", "true");
      fetch("/api/recarga", { method: "POST", headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({ license: topupLicense, amount: eur, currency: "eur", waiver: true }) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.ok || !/^https:\/\/([a-z0-9-]+\.)*(stripe\.com|link\.com)\//.test(d.url || "")) throw new Error(d.error || "No se pudo iniciar el pago.");
          location.href = d.url;
        })
        .catch(function (e) {
          terr.querySelector("span").textContent = e.message || "No se pudo iniciar el pago."; terr.hidden = false;
          go.removeAttribute("aria-busy"); syncTopup();
        });
    });
    syncTopup();
  }
  /* vuelta de Stripe: /saldo/?recarga=cs_… */
  var done = document.querySelector("[data-topup-done]");
  var rsid = done && (new URLSearchParams(location.search).get("recarga") || "");
  if (done && /^cs_[A-Za-z0-9_]{10,250}$/.test(rsid)) {
    var dmsg = done.querySelector("span"), dtries = 0, nfD = new Intl.NumberFormat("es-ES");
    dmsg.textContent = "Pago recibido. Sumando los créditos a tu licencia…"; done.hidden = false;
    (function poll() {
      fetch("/api/recarga?session=" + encodeURIComponent(rsid), { headers: { accept: "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.ok && d.status === "applied") {
            dmsg.textContent = "Recarga completada: +" + nfD.format(d.credits) + " créditos. Saldo actual: " + nfD.format(d.balance) + " créditos.";
            if (bf && bf.license.value) bf.requestSubmit();
            return;
          }
          if (d.ok && d.status === "failed") { dmsg.textContent = "El pago se recibió, pero no pudimos sumar los créditos. Escríbenos a support@keyflint.dev y lo resolvemos o te devolvemos el importe."; return; }
          if (++dtries < 30) setTimeout(poll, 2000);
          else dmsg.textContent = "El pago está confirmado y los créditos se están sumando. Vuelve a consultar el saldo en unos minutos.";
        })
        .catch(function () { if (++dtries < 30) setTimeout(poll, 2000); });
    })();
  }

  /* historial de uso (solo llamadas por URL remota) */
  function loadUsage(lic) {
    var box = document.querySelector("[data-usage]");
    if (!box) return;
    fetch("/api/uso?license=" + encodeURIComponent(lic), { headers: { accept: "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.ok || (!d.recent.length && !d.tools.length)) { box.hidden = true; return; }
        var nf = new Intl.NumberFormat("es-ES"), when = new Intl.DateTimeFormat("es-ES", { dateStyle: "short", timeStyle: "short" });
        function td(v, cls) { var c = document.createElement("td"); if (cls) c.className = cls; c.textContent = v; return c; }
        function fill(sel, rows, cells) {
          var tb = box.querySelector(sel); tb.textContent = "";
          rows.forEach(function (r) { var tr = document.createElement("tr"); cells(r).forEach(function (c) { tr.appendChild(c); }); tb.appendChild(tr); });
        }
        fill("[data-usage-tools]", d.tools, function (r) {
          return [td(r.slug), td(r.tool), td(nf.format(r.calls), "num"), td(nf.format(r.credits || 0), "num"), td(nf.format(r.errors || 0), "num" + (r.errors ? " bad" : ""))];
        });
        fill("[data-usage-recent]", d.recent, function (r) {
          return [td(when.format(new Date(r.ts * 1000))), td(r.slug), td(r.tool), td(nf.format(r.credits || 0), "num"), td(r.ok ? "OK" : "Error", r.ok ? "" : "bad")];
        });
        box.hidden = false;
      })
      .catch(function () { box.hidden = true; });
  }

  /* licencia tras el pago (/gracias/?session_id=cs_…) */
  var rv = document.querySelector("[data-reveal]");
  var sid = rv && (new URLSearchParams(location.search).get("session_id") || "");
  if (rv && /^cs_[A-Za-z0-9_]{10,250}$/.test(sid)) {
    var meta = rv.querySelector("[data-reveal-meta]"), tries = 0;
    rv.hidden = false;
    (function poll() {
      fetch("/api/licencia?session_id=" + encodeURIComponent(sid), { headers: { accept: "application/json" } })
        .then(function (r) { return r.json().then(function (d) { d._s = r.status; return d; }); })
        .then(function (d) {
          if (d.ok && SAFE.test(d.license || "")) {
            rv.querySelector("#lic-reveal").firstChild.textContent = d.license;
            rv.querySelector("[data-reveal-box]").hidden = false;
            meta.textContent = "Plan " + (d.tier || "").replace(/^./, function (c) { return c.toUpperCase(); }) +
              (d.email_hint ? " · enviada a " + d.email_hint : "");
            var lead = document.querySelector("[data-reveal-lead]"); if (lead) lead.textContent = "Tu licencia está lista. Cópiala o ve directo al instalador.";
            store(KEY, d.license); apply(d.license);
            history.replaceState(null, "", location.pathname);
          } else if (d._s === 404 && ++tries < 15) { setTimeout(poll, 2000); }
          else { meta.textContent = d.error || "No pudimos mostrarla aquí. Te llega por correo en unos minutos."; }
        })
        .catch(function () { if (++tries < 15) setTimeout(poll, 2000); else meta.textContent = "No pudimos mostrarla aquí. Te llega por correo en unos minutos."; });
    })();
  }

  /* reenviar licencia */
  var rf = document.querySelector("[data-recover-form]");
  if (rf) {
    var msg = rf.querySelector("[data-recover-msg]");
    rf.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var btn = rf.querySelector("button"), email = rf.email.value.trim();
      if (!rf.email.checkValidity() || !email) { msg.className = "lic-help warn"; msg.textContent = "Escribe un correo válido."; return; }
      btn.disabled = true;
      fetch("/api/recuperar", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: email }) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          msg.className = "lic-help" + (d.ok ? " good" : " warn");
          msg.textContent = d.ok ? "Si ese correo tiene licencias, te llegará un enlace en unos minutos. Revisa spam." : (d.error || "No se pudo enviar.");
        })
        .catch(function () { msg.className = "lic-help warn"; msg.textContent = "No se pudo enviar. Inténtalo en un minuto."; })
        .then(function () { btn.disabled = false; });
    });
  }


  /* estado del servicio (/estado/) */
  var st = document.querySelector("[data-status]");
  if (st) {
    var paint = function (k, ok) {
      var el = st.querySelector('[data-st="' + k + '"]');
      if (el) { el.textContent = ok ? "Funciona" : "Con problemas"; el.className = "st " + (ok ? "st-ok" : "st-bad"); }
    };
    fetch("/api/estado").then(function (r) { return r.json(); }).then(function (d) {
      paint("licenses", d.licenses);
      Object.keys(d.tools || {}).forEach(function (k) { paint(k, d.tools[k]); });
      var t = document.querySelector("[data-st-time]");
      if (t && d.checked) t.textContent = new Date(d.checked).toLocaleString();
    }).catch(function () {
      [].forEach.call(st.querySelectorAll("[data-st]"), function (el) { el.textContent = "Sin respuesta"; el.className = "st st-bad"; });
    });
  }
  /* licencia gratis de prueba (/probar/) */
  var tf = document.querySelector("[data-trial-form]");
  if (tf) {
    var tmsg = tf.querySelector("[data-trial-msg]"), tout = document.querySelector("[data-trial-out]");
    var EN = document.documentElement.lang === "en";
    var M = EN ? { bad: "Enter a valid email.", wait: "Creating your license…", mailed: "Done. It will reach your inbox in a few minutes; check spam.",
      used: "That email already has a trial license.", off: "The free trial is not available right now.", fail: "Could not create the license. Try again in a minute.", net: "Could not connect. Try again in a minute.", rec: "Recover it" }
      : { bad: "Escribe un correo válido.", wait: "Creando tu licencia…", mailed: "Listo. Te llega por correo en unos minutos. Revisa spam.",
      used: null, off: null, fail: "No se pudo crear la licencia.", net: "No se pudo conectar. Inténtalo en un minuto.", rec: "Recuperarla" };
    var say = function (cls, text, link) {
      tmsg.className = "lic-help" + (cls ? " " + cls : ""); tmsg.textContent = text;
      if (link) { var a = document.createElement("a"); a.href = link[0]; a.textContent = link[1]; tmsg.appendChild(document.createTextNode(" ")); tmsg.appendChild(a); }
    };
    tf.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var btn = tf.querySelector("button"), email = tf.email.value.trim();
      if (!tf.email.checkValidity() || !email) { say("warn", M.bad); return; }
      btn.disabled = true; btn.setAttribute("aria-busy", "true"); say("", M.wait);
      fetch("/api/prueba", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: email }) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.ok && d.license && SAFE.test(d.license)) {
            document.getElementById("lic-trial").firstChild.textContent = d.license;
            store(KEY, d.license); apply(d.license);
            tout.hidden = false; tf.hidden = true;
            setTimeout(function () { tout.scrollIntoView({ behavior: "smooth", block: "center" }); }, 50);
          } else if (d.ok && d.emailed) { say("good", M.mailed); }
          else if (d.used) { say("warn", M.used || d.error, ["/gracias/", M.rec]); }
          else if (d.unavailable && M.off) { say("warn", M.off); }
          else { say("warn", (EN ? "" : d.error) || M.fail); }
        })
        .catch(function () { say("warn", M.net); })
        .then(function () { btn.disabled = false; btn.removeAttribute("aria-busy"); });
    });
  }

  /* demos sin instalación en las fichas */
  function el(tag, cls, text) { var x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; }
  function kv(box, pairs) {
    var dl = el("dl", "demo-kv");
    pairs.forEach(function (p) {
      if (p[1] == null || p[1] === "") return;
      var d = el("div"); d.appendChild(el("dt", "", p[0])); d.appendChild(el("dd", "tabnum", String(p[1]))); dl.appendChild(d);
    });
    box.appendChild(dl);
  }
  function issueList(box, list) {
    if (!list || !list.length) return;
    var ul = el("ul", "demo-issues");
    list.forEach(function (i) { ul.appendChild(el("li", i.severity === "error" ? "err" : "", String(i.message || i.detail || JSON.stringify(i)).slice(0, 200))); });
    box.appendChild(ul);
  }
  function codeOut(box, text, label) {
    var wrap = el("div", "code"), head = el("div", "code-head");
    head.appendChild(el("span", "code-label", label || "")); wrap.appendChild(head);
    var p = el("pre"); p.tabIndex = 0; p.appendChild(el("code", "", text)); wrap.appendChild(p); box.appendChild(wrap);
  }
  var RENDER = {
    "web-intel": function (box, r) {
      kv(box, [["Título", r.title], ["Palabras", r.word_count], ["URL final", r.url]]);
      codeOut(box, (r.markdown || "") + (r.truncated ? "\n\n[…recortado en la demo]" : ""), "Markdown");
    },
    norma43: function (box, r) {
      var sm = r.summary || {};
      box.appendChild(el("p", "status " + (r.valid ? "ok" : "warn"), r.valid ? "Fichero válido" : "Fichero con errores"));
      kv(box, [["Cuentas", sm.accounts], ["Movimientos", sm.movements], ["Errores", sm.errors], ["Avisos", sm.warnings]]);
      issueList(box, r.issues);
      (r.accounts || []).forEach(function (a) {
        kv(box, [["Cuenta", a.iban], ["Banco", a.bank], ["Titular", a.holder], ["Saldo inicial", a.opening_balance], ["Saldo final", a.closing_balance]]);
        if (!a.movements || !a.movements.length) return;
        var tw = el("div", "tw"), t = el("table", "uso-t"), th = el("thead"), tr = el("tr"), tb = el("tbody");
        ["Fecha", "Concepto", "Importe"].forEach(function (h, i) { tr.appendChild(el("th", i === 2 ? "num" : "", h)); });
        th.appendChild(tr); t.appendChild(th);
        a.movements.forEach(function (m) {
          var row = el("tr");
          row.appendChild(el("td", "", m.date || ""));
          row.appendChild(el("td", "", m.description || m.concept || ""));
          row.appendChild(el("td", "num tabnum", (m.direction === "cargo" ? "−" : "+") + String(m.amount).replace(/^-/, "")));
          tb.appendChild(row);
        });
        t.appendChild(tb); tw.appendChild(t); box.appendChild(tw);
      });
    },
    contabridge: function (box, r) {
      var sm = r.summary || {};
      kv(box, [["Asientos", sm.entries], ["Líneas", sm.lines], ["Debe", sm.total_debit], ["Haber", sm.total_credit], ["Cuadra", sm.balanced ? "Sí" : "No"]]);
      issueList(box, r.issues);
      codeOut(box, r.content || "", r.filename);
    },
  };
  $$("[data-demo]").forEach(function (f) {
    var slug = f.getAttribute("data-demo"), msg = f.querySelector("[data-demo-msg]"), out = f.querySelector("[data-demo-out]");
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var btn = f.querySelector("button[type=submit]"), body = {};
      $$("input, textarea, select", f).forEach(function (x) { if (x.name) body[x.name] = x.value; });
      btn.disabled = true; btn.setAttribute("aria-busy", "true");
      msg.className = "lic-help"; msg.textContent = "Ejecutando el servidor…"; out.hidden = true;
      fetch("/api/demo/" + slug, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.ok) {
            msg.className = "lic-help warn"; msg.textContent = d.error || "No se pudo ejecutar la demo.";
            if (d.limit) { var a = el("a", "", "Licencia gratis"); a.href = "/probar/"; msg.appendChild(document.createTextNode(" ")); msg.appendChild(a); }
            return;
          }
          out.textContent = ""; RENDER[slug](out, d.result || {}); out.hidden = false;
          msg.className = "lic-help good"; msg.textContent = "Hecho con " + d.tool + ": es lo mismo que recibe tu agente.";
        })
        .catch(function () { msg.className = "lic-help warn"; msg.textContent = "No se pudo conectar. Inténtalo en un minuto."; })
        .then(function () { btn.disabled = false; btn.removeAttribute("aria-busy"); });
    });
  });
})();
