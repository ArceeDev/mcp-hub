// Boletín mensual ("Boletín del cierre") con doble confirmación (Resend) y baja en 1 clic.
// Los correos confirmados solo se guardan tras pulsar el enlace de confirmación (OAUTH_KV).
// Límites diarios por IP y correo atómicos en D1 (hub_limits) para evitar abuso del endpoint.

import { EMAIL_RE, normEmail } from "./emailauth.js";
import { clientIp, giveBack, hash, num, take, today } from "./limits.js";

const PENDING_TTL = 172800; // 48 horas
const TOKEN_RE = /^[0-9a-f]{48}$/;
const SOURCE_RE = /^[a-z0-9_-]{1,32}$/;
const salt = (env) => env.LIMITS_SALT || "kf-hub";

function randomHex(bytes) {
  return Array.from(crypto.getRandomValues(new Uint8Array(bytes)), (b) => b.toString(16).padStart(2, "0")).join("");
}

function originUrl(env) {
  return String(env.PUBLIC_ORIGIN || env.PUBLIC_URL || "https://mcp.keyflint.dev").replace(/\/$/, "");
}

async function sendConfirmationEmail(env, email, confirmUrl) {
  const key = String(env.RESEND_API_KEY || "").trim();
  const from = String(env.EMAIL_FROM || "Flint by KeyFlint <licenses@keyflint.dev>").trim();
  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { authorization: `Bearer ${key}`, "content-type": "application/json", "user-agent": "mcp-hub-newsletter" },
      body: JSON.stringify({
        from,
        to: [email],
        subject: "Confirma tu alta en el Boletín del cierre (Flint by KeyFlint)",
        text:
          "Hola,\n\nHas pedido recibir el Boletín del cierre de Flint by KeyFlint: un correo al mes con guías prácticas de Norma 43, ContaSol, a3 y calendario de cierres.\n\n" +
          `Confirma tu correo en este enlace (caduca en 48 horas):\n${confirmUrl}\n\n` +
          "Si no lo has pedido tú, ignora este mensaje: no guardaremos tu dirección ni volveremos a escribirte.\n\nKeyFlint · support@keyflint.dev",
      }),
      signal: AbortSignal.timeout(8000),
    });
    if (!r.ok) {
      const err = await r.text().catch(() => "");
      console.error("newsletter resend error", r.status, err);
    }
    return r.ok;
  } catch (e) {
    console.error("newsletter resend exception", e?.message);
    return false;
  }
}

export async function startNewsletter(env, request, rawEmail, rawSource = "web") {
  const email = normEmail(rawEmail);
  if (!EMAIL_RE.test(email) || email.length > 254) return { error: "Escribe un correo válido.", status: 400 };
  if (!env.RESEND_API_KEY || !env.OAUTH_KV || !env.USAGE_DB) {
    return { error: "El boletín no está disponible ahora mismo.", status: 503 };
  }
  const source = SOURCE_RE.test(String(rawSource || "")) ? String(rawSource) : "web";
  const mailKey = await hash(email, salt(env));
  const existing = await env.OAUTH_KV.get("sub_mail:" + mailKey, "json");
  if (existing && existing.email) return { ok: true, already: true };

  const ip = clientIp(request);
  if (env.TRIAL_LIMIT) {
    const { success } = await env.TRIAL_LIMIT.limit({ key: "news:" + ip });
    if (!success) return { error: "Demasiados intentos. Espera un minuto.", status: 429 };
  }

  const db = env.USAGE_DB, day = today();
  const ipKey = await hash(ip, salt(env));
  if (!(await take(db, "news_ip", ipKey, day, num(env.NEWSLETTER_PER_IP_DAY, 10)))) {
    return { error: "Se han pedido demasiadas altas desde tu conexión hoy. Vuelve mañana.", status: 429 };
  }
  if (!(await take(db, "news_email", mailKey, day, num(env.NEWSLETTER_PER_EMAIL_DAY, 3)))) {
    await giveBack(db, "news_ip", ipKey, day);
    return { error: "Ya enviamos el enlace de confirmación a este correo hoy. Revisa tu bandeja o spam.", status: 429 };
  }

  const token = randomHex(24);
  await env.OAUTH_KV.put("sub_pending:" + token, JSON.stringify({ email, source, created_at: new Date().toISOString() }), {
    expirationTtl: PENDING_TTL,
  });
  const confirmUrl = `${originUrl(env)}/boletin/confirmar/?token=${token}`;
  let sent = false;
  try { sent = await sendConfirmationEmail(env, email, confirmUrl); } catch (e) { /* red */ }
  if (!sent) {
    await env.OAUTH_KV.delete("sub_pending:" + token);
    await giveBack(db, "news_email", mailKey, day);
    await giveBack(db, "news_ip", ipKey, day);
    return { error: "No pudimos enviar el correo de confirmación. Inténtalo en un minuto.", status: 502 };
  }
  return { ok: true };
}

export async function confirmNewsletter(env, rawToken) {
  const token = String(rawToken || "").trim().toLowerCase();
  if (!TOKEN_RE.test(token)) return { error: "El enlace no es válido.", status: 400 };
  if (!env.OAUTH_KV) return { error: "El servicio no está disponible ahora mismo.", status: 503 };
  const pending = await env.OAUTH_KV.get("sub_pending:" + token, "json");
  if (!pending || !pending.email) {
    return { error: "Este enlace ha caducado o ya se había usado. Puedes apuntarte de nuevo en /boletin/.", status: 400 };
  }
  await env.OAUTH_KV.delete("sub_pending:" + token);

  const email = normEmail(pending.email);
  const mailKey = await hash(email, salt(env));
  const current = await env.OAUTH_KV.get("sub_mail:" + mailKey, "json");
  const unsubToken = current && TOKEN_RE.test(String(current.unsub_token || "")) ? current.unsub_token : randomHex(24);
  await env.OAUTH_KV.put(
    "sub_mail:" + mailKey,
    JSON.stringify({
      email,
      source: pending.source || "web",
      confirmed_at: current?.confirmed_at || new Date().toISOString(),
      unsub_token: unsubToken,
    }),
  );
  await env.OAUTH_KV.put("sub_unsub:" + unsubToken, mailKey);
  return { ok: true, unsub_token: unsubToken };
}

export async function unsubscribeNewsletter(env, rawToken) {
  const token = String(rawToken || "").trim().toLowerCase();
  if (!TOKEN_RE.test(token)) return { error: "El enlace de baja no es válido.", status: 400 };
  if (!env.OAUTH_KV) return { error: "El servicio no está disponible ahora mismo.", status: 503 };
  const mailKey = await env.OAUTH_KV.get("sub_unsub:" + token);
  if (mailKey) {
    await env.OAUTH_KV.delete("sub_mail:" + mailKey);
    await env.OAUTH_KV.delete("sub_unsub:" + token);
    return { ok: true };
  }
  return { ok: true, already: true };
}
