import os

path = r'C:\Users\Usuario\mcp-hub\src\index.js'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

old_page_style = '.auth .logo img{width:28px;height:28px}</style>'
new_page_style = (
    '.auth .logo img{width:28px;height:28px}\n'
    '.auth .lic-opt{border:1px solid var(--line-2);border-radius:10px;padding:12px;margin:8px 0;display:flex;align-items:flex-start;gap:12px;cursor:pointer;background:var(--bg-2);transition:border-color .15s}\n'
    '.auth .lic-opt:hover{border-color:var(--line)}\n'
    '.auth .lic-opt input{width:auto;margin-top:3px;cursor:pointer}\n'
    '.auth details summary{color:var(--muted);cursor:pointer;font-size:.85rem;margin-top:14px}\n'
    '.auth details summary:hover{color:var(--ink)}</style>'
)

assert old_page_style in code, 'old_page_style not found'
code = code.replace(old_page_style, new_page_style, 1)

old_block = """function consentForm(details, handle, error = "") {
  const app = esc(details.clientName || "Una aplicación");
  const who = details.clientDomain
    ? `Publicada por <b>${esc(details.clientDomain)}</b>.`
    : "La aplicación se registró sola; su nombre no está verificado.";
  return `<h1>Conectar ${app}</h1>
<p>${who} El acceso se enviará a <b>${esc(details.redirectHost)}</b>.</p>
${details.redirectIsLoopback ? '<p class="warn">Esto envía el acceso a una aplicación de tu ordenador. Sigue solo si acabas de iniciar la conexión desde ella.</p>' : ""}
<p class="muted">Podrá usar los servidores MCP de KeyFlint con tu licencia y gastar sus créditos. Puedes revocarlo cuando quieras.</p>
<form method="post">
<input type="hidden" name="handle" value="${esc(handle)}">
<label for="lic"><b>Tu licencia</b></label>
<input id="lic" name="license" autocomplete="off" spellcheck="false" placeholder="LIC-…" required>
${error ? `<p class="err">${esc(error)}</p>` : ""}
<p class="muted">¿No tienes? <a href="/probar/" target="_blank" rel="noopener">Consigue una gratis</a> (25 créditos al instante) o <a href="/saldo/#recuperar" target="_blank" rel="noopener">recupérala por correo</a>.</p>
<div class="row"><button class="btn" name="decision" value="deny" formnovalidate>Cancelar</button>
<button class="btn btn-primary" name="decision" value="approve">Conectar</button></div>
</form>`;
}"""

new_block = """function consentForm(details, handle, error = "", emailPrefill = "") {
  const app = esc(details.clientName || "Una aplicación");
  const who = details.clientDomain
    ? `Publicada por <b>${esc(details.clientDomain)}</b>.`
    : "La aplicación se registró sola; su nombre no está verificado.";
  return `<h1>Conectar ${app}</h1>
<p>${who} El acceso se enviará a <b>${esc(details.redirectHost)}</b>.</p>
${details.redirectIsLoopback ? '<p class="warn">Esto envía el acceso a una aplicación de tu ordenador. Sigue solo si acabas de iniciar la conexión desde ella.</p>' : ""}
<p class="muted">Conecta los servidores MCP de KeyFlint para que ${app} pueda procesar facturas, diarios contables y extractos bancarios.</p>
<form method="post">
<input type="hidden" name="handle" value="${esc(handle)}">
<label for="email"><b>Tu correo electrónico</b></label>
<input id="email" name="email" type="email" autocomplete="email" placeholder="nombre@despacho.com" value="${esc(emailPrefill)}" required>
${error ? `<p class="err">${esc(error)}</p>` : ""}
<p class="muted" style="margin-top:6px;font-size:.85rem">Si no tienes licencia, crearemos una prueba gratuita de 25 créditos al instante para este correo.</p>
<details>
  <summary>¿Prefieres introducir tu clave LIC-… directamente?</summary>
  <div style="margin-top:8px">
    <input id="lic" name="license" autocomplete="off" spellcheck="false" placeholder="LIC-…">
  </div>
</details>
<div class="row">
  <button class="btn" name="decision" value="deny" formnovalidate>Cancelar</button>
  <button class="btn btn-primary" name="decision" value="approve">Conectar</button>
</div>
</form>`;
}

function selectLicenseForm(details, handle, email, licenses, error = "") {
  const app = esc(details.clientName || "Una aplicación");
  return `<h1>Elige tu licencia</h1>
<p>Hemos encontrado estas licencias para <b>${esc(email)}</b>. Selecciona con cuál deseas conectar ${app}:</p>
<form method="post">
<input type="hidden" name="handle" value="${esc(handle)}">
<input type="hidden" name="email" value="${esc(email)}">
${licenses.map((lic, i) => `
  <label class="lic-opt">
    <input type="radio" name="license" value="${esc(lic.key)}" ${i === 0 ? "checked" : ""}>
    <div>
      <div><b>${esc(lic.name || ("Licencia " + (lic.tier || "Estándar")))}</b></div>
      <div class="muted" style="font-size:.8rem">${esc(lic.credits != null ? lic.credits + " créditos disponibles" : "Activa")} · <code>${esc(lic.key.slice(0, 12))}…</code></div>
    </div>
  </label>
`).join("")}
${error ? `<p class="err">${esc(error)}</p>` : ""}
<div class="row">
  <button class="btn" name="decision" value="deny" formnovalidate>Cancelar</button>
  <button class="btn btn-primary" name="decision" value="approve">Conectar</button>
</div>
</form>`;
}"""

assert old_block in code, 'old consentForm block not found'
code = code.replace(old_block, new_block, 1)

old_auth_body = """    const approved = await oauth.approveConsent(request, handle, { scope: [SCOPE, "offline_access"] });
    const license = String(form.get("license") || "").trim();
    const state = LICENSE_RE.test(license) ? await licenseExists(env, license) : "format";
    if (state !== "ok") {
      const msg = state === "format" ? "Eso no parece una licencia. Empieza por LIC- y viene en el correo de compra."
        : state === "down" ? "KeyFlint no responde ahora mismo. Inténtalo en un minuto."
          : "No encontramos esa licencia. Revisa que esté completa.";
      const details = await oauth.describeConsent(approved.request);
      const again = await oauth.beginConsent(approved.request);
      return page("Licencia", consentForm(details, again.handle, msg), again.headers, 400);
    }
    const { redirectTo } = await oauth.completeAuthorization({
      request: approved.request,
      userId: await userId(license),
      metadata: { connected: new Date().toISOString() },
      scope: approved.request.scope,
      props: { license },
    });"""

new_auth_body = """    const approved = await oauth.approveConsent(request, handle, { scope: [SCOPE, "offline_access"] });
    let license = String(form.get("license") || "").trim();
    const email = String(form.get("email") || "").trim().toLowerCase();

    // Si no mandó licencia pero sí correo, buscamos o emitimos automáticamente:
    if (!license && email) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        const details = await oauth.describeConsent(approved.request);
        const again = await oauth.beginConsent(approved.request);
        return page("Conectar", consentForm(details, again.handle, "Introduce un correo válido.", email), again.headers, 400);
      }

      // 1. Mirar si ya tiene licencias guardadas en KV para este correo
      let saved = null;
      try {
        if (env.OAUTH_KV) {
          saved = await env.OAUTH_KV.get("email_licenses:" + email, "json");
        }
      } catch (e) {
        console.error("KV read email_licenses error", e?.message);
      }

      if (Array.isArray(saved) && saved.length > 0) {
        if (saved.length === 1) {
          license = saved[0].key;
        } else {
          // Varias licencias: mostrar formulario de selección
          const details = await oauth.describeConsent(approved.request);
          const again = await oauth.beginConsent(approved.request);
          return page("Elige tu licencia", selectLicenseForm(details, again.handle, email, saved), again.headers, 200);
        }
      } else {
        // 2. Nuevo usuario o sin licencia previa: emitir prueba gratuita con KEYFLINT_ADMIN_KEY
        const base = (env.GATEWAY_URL || "https://licenses.keyflint.dev").replace(/\/$/, "");
        if (env.KEYFLINT_ADMIN_KEY) {
          try {
            const r = await fetch(`${base}/api/v1/licenses/issue`, {
              method: "POST",
              headers: {
                "content-type": "application/json",
                "x-admin-key": env.KEYFLINT_ADMIN_KEY,
                "user-agent": "mcp-hub-oauth"
              },
              body: JSON.stringify({
                customer_email: email,
                tier: "community",
                metadata: { trial: true, source: "oauth-mcp-hub" }
              }),
              signal: AbortSignal.timeout(8000)
            });
            const d = await r.json().catch(() => ({}));
            const issued = d?.data?.license_key;
            if (r.ok && issued && LICENSE_RE.test(issued)) {
              license = issued;
              if (env.OAUTH_KV) {
                await env.OAUTH_KV.put("email_licenses:" + email, JSON.stringify([
                  { key: issued, tier: "community", credits: 25, name: "Prueba Gratuita" }
                ]));
              }
            } else if (d?.detail || d?.message) {
              console.warn("issue trial note", d?.detail || d?.message);
            }
          } catch (e) {
            console.error("issue trial error", e?.message);
          }
        }
      }
    }

    const state = LICENSE_RE.test(license) ? await licenseExists(env, license) : "format";
    if (state !== "ok") {
      const msg = state === "format"
        ? (email ? "No encontramos una licencia activa para este correo. Introduce tu clave LIC-… a continuación." : "Eso no parece una licencia. Empieza por LIC-…")
        : state === "down" ? "KeyFlint no responde ahora mismo. Inténtalo en un minuto."
          : "No encontramos esa licencia. Revisa que esté completa.";
      const details = await oauth.describeConsent(approved.request);
      const again = await oauth.beginConsent(approved.request);
      return page("Conectar", consentForm(details, again.handle, msg, email), again.headers, 400);
    }

    // Guardar vinculación email -> licencia si el usuario introdujo ambos
    if (env.OAUTH_KV && email && LICENSE_RE.test(license)) {
      try {
        const existing = (await env.OAUTH_KV.get("email_licenses:" + email, "json")) || [];
        if (!existing.some(l => l.key === license)) {
          existing.push({ key: license, tier: "registrada", name: "Licencia " + license.slice(0, 10) + "…" });
          await env.OAUTH_KV.put("email_licenses:" + email, JSON.stringify(existing));
        }
      } catch (e) {
        console.error("KV save email_licenses error", e?.message);
      }
    }

    const { redirectTo } = await oauth.completeAuthorization({
      request: approved.request,
      userId: await userId(license),
      metadata: { email, connected: new Date().toISOString() },
      scope: approved.request.scope,
      props: { license, email },
    });"""

assert old_auth_body in code, 'old_auth_body not found'
code = code.replace(old_auth_body, new_auth_body, 1)

with open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(code)

print('SUCCESS: Updated index.js with email-first authentication & license selection!')
