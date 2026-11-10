/* KeyFlint MCP: copiar, pestañas, selector de servidor, licencia en vivo y enlaces de 1 clic. */
(function () {
  "use strict";
  var PH = "LIC-tu-licencia", KEY = "kf-mcp-license", SAFE = /^[A-Za-z0-9._~+\/=-]{6,1024}$/;
  /* idioma de la página: las mismas funciones sirven /… y /en/… */
  var EN = document.documentElement.lang === "en", LOC = EN ? "en-US" : "es-ES";
  function T(es, en) { return EN ? en : es; }
  function EUR(n) { return EN ? "€" + n : n + " €"; }
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
      b.classList.add("done"); if (label) label.textContent = T("Copiado", "Copied");
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
      /* "Más clientes" (solo modo remoto): formatos de cada cliente, ver keyflint links */
      var url = cfg.server && cfg.server.url, E = encodeURIComponent;
      if (url) {
        var set = function (id, href) { var a = ins.querySelector('[data-deeplink="' + id + '"]'); if (a) a.href = href; };
        set("goose", "goose://extension?url=" + E(url) + "&type=streamable_http&id=" + E(cfg.slug) +
          "&name=" + E(cfg.name || cfg.slug) + "&description=" + E(cfg.desc || ""));
        set("lmstudio", "lmstudio://add_mcp?name=" + E(cfg.slug) + "&config=" +
          E(b64(JSON.stringify({ url: url, headers: { Authorization: "Bearer " + value } }))));
        set("kiro", "https://kiro.dev/launch/mcp/add?name=" + E(cfg.slug) + "&config=" + E(JSON.stringify({ url: url })));
        set("vscode-insiders", "vscode-insiders:mcp/install?" + E(JSON.stringify({ name: cfg.slug, type: "http", url: url })));
      }
      var input = ins.querySelector("[data-license]"), state = ins.querySelector("[data-license-state]"), help = ins.querySelector(".lic-help");
      if (input && document.activeElement !== input) input.value = lic || "";
      if (state) state.innerHTML = ok ? CHECK : "";
      if (help) {
        var bad = !!lic && !ok;
        help.classList.toggle("warn", bad);
        help.textContent = bad ? T("Esa licencia tiene caracteres no válidos. Cópiala de nuevo desde el correo.", "That license has invalid characters. Copy it again from the email.") :
          ok ? T("Licencia aplicada en todos los fragmentos y botones.", "License applied to every snippet and button.") : T("Se rellena en todos los fragmentos. No sale de tu navegador.", "Fills in every snippet. It never leaves your browser.");
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

  /* enlace del correo de saldo agotado: /saldo/#licencia=…&importe=5 (la licencia sale de la barra de direcciones) */
  var HASH = new URLSearchParams((location.hash || "").replace(/^#/, ""));
  if (HASH.get("licencia") && history.replaceState) history.replaceState(null, "", location.pathname + location.search + "#recargar");

  /* saldo */
  var bf = document.querySelector("[data-balance-form]");
  if (bf) {
    var out = document.querySelector("[data-balance-out]"), err = document.querySelector("[data-balance-err]");
    var nf = new Intl.NumberFormat(LOC);
    var TIERS = { community: T("Gratis", "Free"), pro: "Pro", indie: "Indie", agency: "Agency", studio: "Studio", lifetime: "Founder" };
    var STATUS = EN ? { active: "Active", grace_period: "Grace period", expired: "Expired", suspended: "Suspended", revoked: "Revoked" }
      : { active: "Activa", grace_period: "En periodo de gracia", expired: "Caducada", suspended: "Suspendida", revoked: "Revocada" };
    function cleanLicense(raw) {
      if (!raw) return "";
      var str = String(raw).trim();
      var m = str.match(/LIC-[A-Za-z0-9._~+\/=-]{10,}/);
      if (m) return m[0];
      return str.replace(/[\s"'`]/g, "");
    }
    function f(name, v) { var el = out.querySelector('[data-f="' + name + '"]'); if (el) el.textContent = v; }

    var qLic = new URLSearchParams(window.location.search).get("licencia") || new URLSearchParams(window.location.search).get("license") || HASH.get("licencia");
    if (qLic) {
      bf.license.value = cleanLicense(qLic);
      setTimeout(function () { bf.dispatchEvent(new Event("submit")); }, 50);
    } else if (!bf.license.value) {
      bf.license.value = cleanLicense(store(KEY) || "");
      if (bf.license.value && (location.hash === "#recargar" || HASH.get("importe"))) {
        setTimeout(function () { bf.dispatchEvent(new Event("submit")); }, 50);
      }
    }

    bf.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var lic = cleanLicense(bf.license.value), btn = bf.querySelector("button");
      bf.license.value = lic;
      out.hidden = true; err.hidden = true;
      if (!lic) {
        err.querySelector("span").textContent = T("Introduce o pega tu clave de licencia (empieza por LIC-).", "Enter or paste your license key (starts with LIC-).");
        err.hidden = false;
        return;
      }
      if (!SAFE.test(lic)) {
        err.querySelector("span").textContent = T("Pega la licencia completa, tal como aparece en el correo.", "Paste the full license, exactly as it appears in the email.");
        err.hidden = false;
        return;
      }
      btn.disabled = true; btn.setAttribute("aria-busy", "true");
      fetch("/api/saldo?license=" + encodeURIComponent(lic), { headers: { accept: "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.ok) throw new Error((EN ? "License not found or unavailable. Check that you pasted the full key." : d.error) || T("No se pudo consultar el saldo.", "Could not check the balance."));
          f("tier", T("Plan ", "") + (TIERS[d.tier] || d.tier) + T("", " plan")); f("status", STATUS[d.status] || d.status);
          out.querySelector('[data-f="status"]').className = "status" + (d.status === "active" ? " ok" : " warn");
          f("balance", nf.format(d.balance)); f("consumed", nf.format(d.consumed)); f("allowance", nf.format(d.allowance));
          var m = out.querySelector("[data-meter]"), pct = d.allowance ? Math.max(0, Math.min(100, d.balance / d.allowance * 100)) : 0;
          m.setAttribute("aria-valuemax", d.allowance); m.setAttribute("aria-valuenow", d.balance);
          m.setAttribute("aria-label", nf.format(d.balance) + T(" de ", " of ") + nf.format(d.allowance) + T(" créditos", " credits"));
          m.firstElementChild.style.width = pct + "%"; m.classList.toggle("low", pct < 15);
          out.hidden = false;
          store(KEY, lic);
          topupLicense = d.status === "active" || d.status === "grace_period" ? lic : "";
          syncTopup(); if (location.hash === "#recargar" || HASH.get("importe")) { var rEl = document.getElementById("recargar"); if (rEl) setTimeout(function () { rEl.scrollIntoView({ behavior: "smooth", block: "start" }); }, 60); }
          loadUsage(lic);
        })
        .catch(function (e) { err.querySelector("span").textContent = e.message || T("No se pudo consultar el saldo.", "Could not check the balance."); err.hidden = false; })
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
    var nfT = new Intl.NumberFormat(LOC);
    function bonusOf(eur) { var b = 0; cfg.tiers.forEach(function (t) { if (eur >= t[0]) b = t[1]; }); return b; }
    function creditsOf(eur) { return eur < cfg.min ? 0 : Math.floor(eur * 100 * cfg.rate * (100 + bonusOf(eur)) / 10000); }
    function valid(eur) { return Number.isInteger(eur) && eur >= cfg.min && eur <= cfg.max; }
    syncTopup = function () {
      var eur = Number(amt.value), ok = valid(eur), b = bonusOf(eur), c = creditsOf(eur);
      tb.querySelector("[data-topup-credits]").textContent = ok ? nfT.format(c) : "—";
      var bonus = tb.querySelector("[data-topup-bonus]"); bonus.hidden = !ok || !b; bonus.textContent = "+" + b + T(" %", "%");
      var eqMsg = tb.querySelector("[data-topup-eq]"); eqMsg.hidden = ok; eqMsg.textContent = T("Entre ", "Between ") + EUR(cfg.min) + T(" y ", " and ") + EUR(cfg.max) + T(", sin decimales", ", whole euros");
      tb.querySelector("[data-topup-eqs]").hidden = !ok;
      tb.querySelectorAll("[data-eq]").forEach(function (el) { el.textContent = "≈ " + nfT.format(Math.floor(c / Number(el.getAttribute("data-eq")))); });
      if (bonus.getAttribute("data-b") !== String(b)) { bonus.setAttribute("data-b", b); bonus.classList.remove("pop"); requestAnimationFrame(function () { bonus.classList.add("pop"); }); }
      rng.style.setProperty("--p", Math.max(0, Math.min(100, (Number(rng.value) - Number(rng.min)) / (Number(rng.max) - Number(rng.min)) * 100)) + "%");
      var next = cfg.tiers.filter(function (t) { return t[0] > eur; })[0];
      tb.querySelector("[data-topup-next]").textContent = ok && next
        ? T("Con " + EUR(next[0]) + " (" + EUR(next[0] - eur) + " más) recibes " + nfT.format(creditsOf(next[0])) + " créditos: +" + next[1] + " %.",
            "With " + EUR(next[0]) + " (" + EUR(next[0] - eur) + " more) you get " + nfT.format(creditsOf(next[0])) + " credits: +" + next[1] + "%.") : "";
      tb.querySelectorAll("[data-tier-min]").forEach(function (li) {
        var m = Number(li.getAttribute("data-tier-min")), nx = cfg.tiers.filter(function (t) { return t[0] > m; })[0];
        li.classList.toggle("on", ok && eur >= m && (!nx || eur < nx[0]));
        li.setAttribute("aria-pressed", String(ok && eur === m));
      });
      tb.querySelector("[data-topup-label]").textContent = ok ? T("Recargar ", "Top up ") + EUR(eur) : T("Recargar", "Top up");
      go.disabled = !(ok && waiver.checked && topupLicense);
    };
    rng.addEventListener("input", function () { amt.value = rng.value; syncTopup(); });
    amt.addEventListener("input", function () { var v = Number(amt.value); if (v >= cfg.min && v <= Number(rng.max)) rng.value = v; syncTopup(); });
    waiver.addEventListener("change", syncTopup);
    tb.querySelectorAll("[data-preset]").forEach(function (btn) {
      btn.addEventListener("click", function () { var v = btn.getAttribute("data-preset"); amt.value = v; rng.value = v; syncTopup(); });
    });
    go.addEventListener("click", function () {
      var eur = Number(amt.value);
      if (!valid(eur) || !waiver.checked || !topupLicense) return;
      terr.hidden = true; go.disabled = true; go.setAttribute("aria-busy", "true");
      fetch("/api/recarga", { method: "POST", headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({ license: topupLicense, amount: eur, currency: "eur", waiver: true, lang: EN ? "en" : "es" }) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.ok || !/^https:\/\/([a-z0-9-]+\.)*(stripe\.com|link\.com)\//.test(d.url || "")) throw new Error(d.error || T("No se pudo iniciar el pago.", "Could not start the payment."));
          location.href = d.url;
        })
        .catch(function (e) {
          terr.querySelector("span").textContent = e.message || T("No se pudo iniciar el pago.", "Could not start the payment."); terr.hidden = false;
          go.removeAttribute("aria-busy"); syncTopup();
        });
    });
    var hAmt = Number(HASH.get("importe"));
    if (valid(hAmt)) { amt.value = hAmt; if (hAmt <= Number(rng.max)) rng.value = hAmt; }
    syncTopup();
  }
  /* vuelta de Stripe: /saldo/?recarga=cs_… */
  var done = document.querySelector("[data-topup-done]");
  var rsid = done && (new URLSearchParams(location.search).get("recarga") || "");
  if (done && /^cs_[A-Za-z0-9_]{10,250}$/.test(rsid)) {
    var dmsg = done.querySelector("span"), dtries = 0, nfD = new Intl.NumberFormat(LOC);
    dmsg.textContent = T("Pago recibido. Sumando los créditos a tu licencia…", "Payment received. Adding the credits to your license…"); done.hidden = false;
    (function poll() {
      fetch("/api/recarga?session=" + encodeURIComponent(rsid), { headers: { accept: "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.ok && d.status === "applied") {
            dmsg.textContent = T("Recarga completada: +", "Top-up complete: +") + nfD.format(d.credits) + T(" créditos. Saldo actual: ", " credits. Current balance: ") + nfD.format(d.balance) + T(" créditos.", " credits.");
            if (bf && bf.license.value) bf.requestSubmit();
            return;
          }
          if (d.ok && d.status === "failed") { dmsg.textContent = T("El pago se recibió, pero no pudimos sumar los créditos. Escríbenos a support@keyflint.dev y lo resolvemos o te devolvemos el importe.", "The payment arrived but we could not add the credits. Email support@keyflint.dev and we will fix it or refund you."); return; }
          if (++dtries < 30) setTimeout(poll, 2000);
          else dmsg.textContent = T("El pago está confirmado y los créditos se están sumando. Vuelve a consultar el saldo en unos minutos.", "Payment confirmed and the credits are being added. Check your balance again in a few minutes.");
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
        var nf = new Intl.NumberFormat(LOC), when = new Intl.DateTimeFormat(LOC, { dateStyle: "short", timeStyle: "short" });
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
      if (!rf.email.checkValidity() || !email) { msg.className = "lic-help warn"; msg.textContent = T("Escribe un correo válido.", "Enter a valid email."); return; }
      btn.disabled = true;
      fetch("/api/recuperar", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: email }) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          msg.className = "lic-help" + (d.ok ? " good" : " warn");
          msg.textContent = d.ok ? T("Si ese correo tiene licencias, te llegará un enlace en unos minutos. Revisa spam.", "If that email has licenses, a one-time link will arrive in a few minutes. Check spam.") : ((EN ? "" : d.error) || T("No se pudo enviar.", "Could not send the link."));
        })
        .catch(function () { msg.className = "lic-help warn"; msg.textContent = T("No se pudo enviar. Inténtalo en un minuto.", "Could not send. Try again in a minute."); })
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
          else if (d.used) { say("warn", M.used || d.error, [T("/saldo/#recuperar", "/en/balance/#recuperar"), M.rec]); }
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
      kv(box, [[T("Título", "Title"), r.title], [T("Palabras", "Words"), r.word_count], [T("URL final", "Final URL"), r.url]]);
      codeOut(box, (r.markdown || "") + (r.truncated ? T("\n\n[…recortado en la demo]", "\n\n[…truncated in the demo]") : ""), "Markdown");
    },
    norma43: function (box, r) {
      var sm = r.summary || {};
      box.appendChild(el("p", "status " + (r.valid ? "ok" : "warn"), r.valid ? T("Fichero válido", "Valid file") : T("Fichero con errores", "File has errors")));
      kv(box, [[T("Cuentas", "Accounts"), sm.accounts], [T("Movimientos", "Movements"), sm.movements], [T("Errores", "Errors"), sm.errors], [T("Avisos", "Warnings"), sm.warnings]]);
      issueList(box, r.issues);
      (r.accounts || []).forEach(function (a) {
        kv(box, [[T("Cuenta", "Account"), a.iban], [T("Banco", "Bank"), a.bank], [T("Titular", "Holder"), a.holder], [T("Saldo inicial", "Opening balance"), a.opening_balance], [T("Saldo final", "Closing balance"), a.closing_balance]]);
        if (!a.movements || !a.movements.length) return;
        var tw = el("div", "tw"), t = el("table", "uso-t"), th = el("thead"), tr = el("tr"), tb = el("tbody");
        [T("Fecha", "Date"), T("Concepto", "Description"), T("Importe", "Amount")].forEach(function (h, i) { tr.appendChild(el("th", i === 2 ? "num" : "", h)); });
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
      kv(box, [[T("Asientos", "Entries"), sm.entries], [T("Líneas", "Lines"), sm.lines], [T("Debe", "Debit"), sm.total_debit], [T("Haber", "Credit"), sm.total_credit], [T("Cuadra", "Balanced"), sm.balanced ? T("Sí", "Yes") : "No"]]);
      issueList(box, r.issues);
      codeOut(box, r.content || "", r.filename);
    },
  };
  /* playground: pestañas de demos */
  $$("[data-live]").forEach(function (b) {
    b.addEventListener("click", function () {
      var slug = b.getAttribute("data-live"), box = b.closest("section");
      $$("[data-live]", box).forEach(function (x) { x.setAttribute("aria-selected", x === b ? "true" : "false"); });
      $$("[data-live-panel]", box).forEach(function (p) { p.hidden = p.getAttribute("data-live-panel") !== slug; });
    });
  });

  /* calculadora de ahorro (precios y /asesorias/) */
  $$("[data-roi]").forEach(function (f) {
    var cfg = JSON.parse(f.getAttribute("data-roi"));
    var eur = new Intl.NumberFormat(LOC, { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
    var eur2 = new Intl.NumberFormat(LOC, { style: "currency", currency: "EUR", minimumFractionDigits: 2, maximumFractionDigits: 2 });
    var num = new Intl.NumberFormat(LOC, { maximumFractionDigits: 1 });
    function v(n) { var x = Number(f.elements[n].value); return isFinite(x) && x > 0 ? x : 0; }
    function put(k, t) { var el = f.querySelector("[data-roi-" + k + "]"); if (el) el.textContent = t; }
    function calc() {
      var t = cfg.tasks[f.elements.task.value], n = v("n"), rate = v("rate");
      var saved = Math.max(0, v("manual") - v("review")) * n / 60, manual = v("manual") * n / 60 * rate;
      var credits = t[0] * n, flint = credits * cfg.eur_per_credit + v("review") * n / 60 * rate;
      put("hours", num.format(saved) + " h"); put("manual", eur.format(manual));
      put("flint", eur.format(flint)); put("credits", eur2.format(credits * cfg.eur_per_credit) + T(" en créditos + tu revisión", " in credits + your review"));
      put("save", eur.format(Math.max(0, manual - flint))); put("cpu", t[0]);
    }
    f.elements.task.addEventListener("change", function () {
      var t = cfg.tasks[f.elements.task.value];
      f.elements.n.value = t[1]; f.elements.manual.value = t[2]; f.elements.review.value = t[3]; calc();
    });
    f.addEventListener("input", calc);
    f.addEventListener("submit", function (ev) { ev.preventDefault(); });
    calc();
  });

  $$("[data-demo]").forEach(function (f) {
    var slug = f.getAttribute("data-demo"), msg = f.querySelector("[data-demo-msg]"), out = f.querySelector("[data-demo-out]");
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var btn = f.querySelector("button[type=submit]"), body = {};
      $$("input, textarea, select", f).forEach(function (x) { if (x.name) body[x.name] = x.value; });
      btn.disabled = true; btn.setAttribute("aria-busy", "true");
      msg.className = "lic-help"; msg.textContent = T("Ejecutando el servidor…", "Running the server…"); out.hidden = true;
      fetch("/api/demo/" + slug, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.ok) {
            msg.className = "lic-help warn";
            msg.textContent = EN ? (d.limit ? "You've used today's demo runs. Get a free license to keep going." : d.unavailable ? "The demo is not available right now." : "Could not run the demo: " + (d.error || "unknown error"))
              : (d.error || "No se pudo ejecutar la demo.");
            if (d.limit) { var a = el("a", "", T("Licencia gratis", "Free license")); a.href = T("/probar/", "/en/try/"); msg.appendChild(document.createTextNode(" ")); msg.appendChild(a); }
            return;
          }
          out.textContent = ""; RENDER[slug](out, d.result || {}); out.hidden = false;
          msg.className = "lic-help good"; msg.textContent = T("Hecho con " + d.tool + ": es lo mismo que recibe tu agente.", "Done with " + d.tool + ": exactly what your agent gets.");
        })
        .catch(function () { msg.className = "lic-help warn"; msg.textContent = T("No se pudo conectar. Inténtalo en un minuto.", "Could not connect. Try again in a minute."); })
        .then(function () { btn.disabled = false; btn.removeAttribute("aria-busy"); });
    });
  });
})();
