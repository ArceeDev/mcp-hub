// Acceso por correo en /authorize: el correo solo vale si quien lo escribe demuestra que lo controla.
// Código de 6 dígitos por correo (Resend), 10 min de vida, 5 fallos por código, límites diarios por correo e IP (D1).
// Tras verificar: sesión corta en KV con la que elegir licencia, añadir una LIC- o pedir la prueba (1 por correo para siempre,
// mismo contador que /probar/). La lista correo -> licencias solo se escribe con correo verificado.

import { clientIp, giveBack, hash, num, take, today } from "./limits.js";

export const EMAIL_RE = /^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$/;
const CODE_TTL = 600, SESSION_TTL = 900, MAX_TRIES = 5;
const salt = (env) => env.LIMITS_SALT || "kf-hub";

export function normEmail(v) {
  return String(v || "").trim().toLowerCase();
}

function randomHex(bytes) {
  return Array.from(crypto.getRandomValues(new Uint8Array(bytes)), (b) => b.toString(16).padStart(2, "0")).join("");
}

function newCode() {
  const b = crypto.getRandomValues(new Uint32Array(1))[0];
  return String(b % 1_000_000).padStart(6, "0");
}

function sameHex(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

async function sendCode(env, email, code) {
  const key = String(env.RESEND_API_KEY || "").trim();
  const from = String(env.EMAIL_FROM || "Flint by KeyFlint <licenses@keyflint.dev>").trim();
  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { authorization: `Bearer ${key}`, "content-type": "application/json", "user-agent": "mcp-hub-oauth" },
      body: JSON.stringify({
        from,
        to: [email],
        subject: `Tu código de acceso a Flint: ${code}`,
        text: `Tu código para conectar Flint by KeyFlint es ${code}\n\nCaduca en 10 minutos. Si no lo has pedido tú, ignora este correo: nadie puede usar tu licencia sin este código.\n\nKeyFlint · support@keyflint.dev`,
      }),
      signal: AbortSignal.timeout(8000),
    });
    if (!r.ok) {
      const err = await r.text().catch(() => "");
      console.error("resend email error", r.status, err);
    }
    return r.ok;
  } catch (e) {
    console.error("resend fetch exception", e?.message);
    return false;
  }
}

// Envía un código nuevo. {ok} o {error, status}.
export async function startEmailLogin(env, request, email) {
  if (!EMAIL_RE.test(email) || email.length > 254) return { error: "Introduce un correo válido.", status: 400 };
  if (!env.RESEND_API_KEY || !env.USAGE_DB || !env.OAUTH_KV)
    return { error: "El acceso por correo no está disponible ahora mismo. Usa tu clave LIC-… más abajo.", status: 503 };
  const ip = clientIp(request);
  if (env.TRIAL_LIMIT) {
    const { success } = await env.TRIAL_LIMIT.limit({ key: "otp:" + ip });
    if (!success) return { error: "Demasiados intentos. Espera un minuto.", status: 429 };
  }
  const db = env.USAGE_DB, day = today();
  const ipKey = await hash(ip, salt(env)), mailKey = await hash(email, salt(env));
  if (!(await take(db, "otp_ip", ipKey, day, num(env.OTP_PER_IP_DAY, 10))))
    return { error: "Se han pedido demasiados códigos desde tu conexión hoy. Vuelve mañana.", status: 429 };
  if (!(await take(db, "otp_email", mailKey, day, num(env.OTP_PER_EMAIL_DAY, 5)))) {
    await giveBack(db, "otp_ip", ipKey, day);
    return { error: "Ya enviamos varios códigos a este correo hoy. Usa el último o vuelve mañana.", status: 429 };
  }
  const code = newCode(), id = randomHex(8);
  await env.OAUTH_KV.put("otp:" + mailKey, JSON.stringify({ id, h: await hash(code, salt(env) + mailKey) }), { expirationTtl: CODE_TTL });
  let sent = false;
  try { sent = await sendCode(env, email, code); } catch (e) { /* red */ }
  if (!sent) {
    await env.OAUTH_KV.delete("otp:" + mailKey);
    await giveBack(db, "otp_email", mailKey, day);
    await giveBack(db, "otp_ip", ipKey, day);
    console.error("otp send failed");
    return { error: "No pudimos enviar el código. Inténtalo en un minuto o usa tu clave LIC-….", status: 502 };
  }
  return { ok: true };
}

// Comprueba el código. Fallos contados en D1 (atómico): 5 por código y luego hay que pedir otro.
export async function verifyEmailCode(env, email, code) {
  if (!env.USAGE_DB || !env.OAUTH_KV) return { error: "El acceso por correo no está disponible ahora mismo.", status: 503 };
  const mailKey = await hash(email, salt(env));
  const saved = await env.OAUTH_KV.get("otp:" + mailKey, "json");
  if (!saved || !saved.id) return { error: "El código ha caducado. Pide uno nuevo.", status: 400, expired: true };
  const clean = String(code || "").replace(/\s+/g, "");
  if (/^\d{6}$/.test(clean) && sameHex(await hash(clean, salt(env) + mailKey), saved.h)) {
    await env.OAUTH_KV.delete("otp:" + mailKey);
    return { ok: true };
  }
  if (!(await take(env.USAGE_DB, "otp_try", mailKey + ":" + saved.id, today(), MAX_TRIES - 1))) {
    await env.OAUTH_KV.delete("otp:" + mailKey);
    return { error: "Demasiados intentos con este código. Pide uno nuevo.", status: 429, expired: true };
  }
  return { error: "Código incorrecto. Revisa el último correo que te enviamos.", status: 400 };
}

export async function openSession(env, email) {
  const token = randomHex(24);
  await env.OAUTH_KV.put("vsess:" + token, email, { expirationTtl: SESSION_TTL });
  return token;
}

export async function readSession(env, token) {
  if (!/^[0-9a-f]{48}$/.test(String(token || "")) || !env.OAUTH_KV) return "";
  return normEmail(await env.OAUTH_KV.get("vsess:" + token));
}

export async function closeSession(env, token) {
  if (/^[0-9a-f]{48}$/.test(String(token || ""))) await env.OAUTH_KV.delete("vsess:" + token);
}

// Licencias enlazadas a un correo verificado (prefijo nuevo: las de "email_licenses:" se crearon sin verificar y se ignoran).
export async function licensesFor(env, email) {
  const norm = normEmail(email);
  if (!norm) return [];
  const k = "mail_lic:" + (await hash(norm, salt(env)));

  // 1. Consultar KV local primero
  if (env.OAUTH_KV) {
    const list = await env.OAUTH_KV.get(k, "json");
    if (Array.isArray(list) && list.length > 0) {
      return list.filter((l) => l && typeof l.key === "string");
    }
  }

  // 2. Si no hay en KV, consultar la pasarela central (keyflint-gateway)
  if (env.KEYFLINT_ADMIN_KEY) {
    try {
      const base = (env.GATEWAY_URL || "https://licenses.keyflint.dev").replace(/\/$/, "");
      const res = await fetch(`${base}/api/v1/licenses/by-customer?email=${encodeURIComponent(norm)}`, {
        headers: { "x-admin-key": env.KEYFLINT_ADMIN_KEY, accept: "application/json", "user-agent": "mcp-hub-oauth" },
        signal: AbortSignal.timeout(6000),
      });
      if (res.ok) {
        const d = await res.json().catch(() => ({}));
        const fromGateway = Array.isArray(d?.data) ? d.data : [];
        if (fromGateway.length > 0) {
          const formatted = fromGateway.map((lic) => ({
            key: lic.key,
            tier: lic.tier || "registrada",
            name: lic.name || `Licencia ${(lic.tier || "").toUpperCase()}`,
          }));
          if (env.OAUTH_KV) {
            await env.OAUTH_KV.put(k, JSON.stringify(formatted.slice(0, 20)));
          }
          return formatted;
        }
      }
    } catch (e) {
      console.error("gateway licenses lookup error", e?.message || e);
    }
  }

  return [];
}

export async function bindLicense(env, email, entry) {
  const norm = normEmail(email);
  if (!norm || !env.OAUTH_KV) return;
  const k = "mail_lic:" + (await hash(norm, salt(env)));
  const list = (await env.OAUTH_KV.get(k, "json")) || [];
  if (!list.some((l) => l.key === entry.key)) {
    list.push(entry);
    await env.OAUTH_KV.put(k, JSON.stringify(list.slice(-20)));
  }
}

// Prueba de 25 créditos para un correo ya verificado. Comparte contadores con /api/prueba.
export async function issueTrial(env, request, email) {
  const db = env.USAGE_DB;
  if (!db || !env.KEYFLINT_ADMIN_KEY) return { error: "La prueba gratis no está activa ahora mismo.", status: 503 };
  const day = today(), ipKey = await hash(clientIp(request), salt(env)), mailKey = await hash(email, salt(env));
  if (!(await take(db, "trial_ip", ipKey, day, num(env.TRIAL_PER_IP_DAY, 2))))
    return { error: "Ya se han pedido varias pruebas desde tu conexión hoy. Vuelve mañana.", status: 429 };
  if (!(await take(db, "trial_email", mailKey, 0, 1))) {
    await giveBack(db, "trial_ip", ipKey, day);
    return { error: "Este correo ya usó su prueba gratis. Pega tu clave LIC-… o recupérala en /saldo/.", status: 409 };
  }
  const undo = async () => { await giveBack(db, "trial_email", mailKey, 0); await giveBack(db, "trial_ip", ipKey, day); };
  try {
    const base = (env.GATEWAY_URL || "https://licenses.keyflint.dev").replace(/\/$/, "");
    const r = await fetch(`${base}/api/v1/licenses/issue`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-admin-key": env.KEYFLINT_ADMIN_KEY, "user-agent": "mcp-hub-oauth" },
      body: JSON.stringify({ customer_email: email, tier: "community", metadata: { trial: true, source: "oauth-mcp-hub" } }),
      signal: AbortSignal.timeout(8000),
    });
    const d = await r.json().catch(() => ({}));
    const key = String(d?.data?.license_key || "");
    if (!r.ok || !/^LIC-[A-Za-z0-9._~+\/=-]{6,1024}$/.test(key)) { await undo(); return { error: "KeyFlint no responde ahora mismo. Inténtalo en un minuto.", status: 502 }; }
    await bindLicense(env, email, { key, tier: "community", name: "Prueba gratuita" });
    return { ok: true, license: key };
  } catch (e) {
    await undo();
    return { error: "KeyFlint no responde ahora mismo. Inténtalo en un minuto.", status: 502 };
  }
}
