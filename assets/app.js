/* KeyFlint MCP: copiar, pestañas, selector de servidor, licencia en vivo y enlaces de 1 clic. */
(function () {
  "use strict";
  var PH = "LIC-tu-licencia", KEY = "kf-mcp-license", SAFE = /^[A-Za-z0-9._~+\/=-]{6,400}$/;
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
        })
        .catch(function (e) { err.querySelector("span").textContent = e.message || "No se pudo consultar el saldo."; err.hidden = false; })
        .then(function () { btn.disabled = false; btn.removeAttribute("aria-busy"); });
    });
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
})();
