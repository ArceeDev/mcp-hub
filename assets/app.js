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
      cfg.server.env.KEYFLINT_LICENSE = value;
      $$("pre", ins).forEach(function (pre) {
        pre.firstChild.textContent = pre.getAttribute("data-tpl").split(PH).join(value);
      });
      var c = ins.querySelector('[data-deeplink="cursor"]');
      if (c) c.href = "cursor://anysphere.cursor-deeplink/mcp/install?name=" + encodeURIComponent(cfg.slug) +
        "&config=" + encodeURIComponent(b64(JSON.stringify(cfg.server)));
      var v = ins.querySelector('[data-deeplink="vscode"]');
      if (v) v.href = "vscode:mcp/install?" + encodeURIComponent(JSON.stringify({
        name: cfg.slug, type: "stdio", command: cfg.server.command, args: cfg.server.args, env: cfg.server.env }));
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
})();
