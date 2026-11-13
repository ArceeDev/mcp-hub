// Solicitud de piloto gratis de 30 días para despachos (/piloto/).
// El despacho pide que le contactemos: se guarda en D1 (pilots) y se avisa a Arcee por Resend con reply-to al despacho.
// Sin envío comercial al solicitante (LSSI art. 21): solo el aviso interno.
import { EMAIL_RE, normEmail } from "./emailauth.js";
import { clientIp, hash, take, today } from "./limits.js";

export const PROGRAMS = ["contasol", "a3", "contaplus", "sage50", "holded", "excel", "otro"];
export const SIZES = ["1-10", "11-30", "31-100", "100+"];
const clean = (v, max) => String(v ?? "").replace(/[\u0000-\u001f\u007f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
const TOKEN_RE = /^[a-z0-9._-]{1,40}$/;

export function parsePilot(b) {
  const email = normEmail(b?.email);
  const p = {
    email, nombre: clean(b?.nombre, 80), despacho: clean(b?.despacho, 120),
    programa: String(b?.programa || ""), clientes: String(b?.clientes || ""),
    telefono: clean(b?.telefono, 30).replace(/[^0-9+ ]/g, ""), mensaje: clean(b?.mensaje, 600),
    origen: TOKEN_RE.test(String(b?.origen || "").toLowerCase()) ? String(b.origen).toLowerCase() : "",
  };
  if (!EMAIL_RE.test(email) || email.length > 254) return { error: "Escribe un correo válido." };
  if (p.nombre.length < 2 || p.despacho.length < 2) return { error: "Indica tu nombre y el del despacho." };
  if (!PROGRAMS.includes(p.programa)) return { error: "Elige el programa contable." };
  if (!SIZES.includes(p.clientes)) return { error: "Elige cuántos clientes lleváis." };
  if (b?.acepto !== true) return { error: "Necesitamos tu permiso para contactarte sobre el piloto." };
  if (String(b?.web || "")) return { spam: true }; // honeypot
  return { ok: true, p };
}

async function notify(env, p) {
  const key = String(env.RESEND_API_KEY || "").trim();
  const to = String(env.PILOT_EMAIL || env.REPORT_EMAIL || "").trim();
  if (!key || !to) return false;
  const from = String(env.EMAIL_FROM || "Flint by KeyFlint <licenses@keyflint.dev>").trim();
  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { authorization: `Bearer ${key}`, "content-type": "application/json", "user-agent": "mcp-hub-pilot" },
      body: JSON.stringify({
        from, to: [to], reply_to: p.email,
        subject: `Piloto Flint: ${p.despacho} (${p.programa}, ${p.clientes} clientes)`,
        text: [
          "Nueva solicitud de piloto de 30 días.", "",
          `Nombre: ${p.nombre}`, `Despacho: ${p.despacho}`, `Correo: ${p.email}`, `Teléfono: ${p.telefono || "-"}`,
          `Programa: ${p.programa}`, `Clientes: ${p.clientes}`, `Origen: ${p.origen || "-"}`, "", `Mensaje: ${p.mensaje || "-"}`, "",
          "Responde a este correo para escribirle (ha dado su permiso). Guion: ventas/captacion/guion-demo-10min.md",
        ].join("\n"),
      }),
      signal: AbortSignal.timeout(8000),
    });
    return r.ok;
  } catch { return false; }
}

export async function requestPilot(env, request, body) {
  const v = parsePilot(body);
  if (v.spam) return { ok: true };
  if (v.error) return { error: v.error, status: 400 };
  const db = env.USAGE_DB;
  if (!db) return { error: "No disponible ahora mismo. Escríbenos a support@keyflint.dev.", status: 503 };
  const day = today(), salt = env.LIMITS_SALT || "kf-hub";
  if (!(await take(db, "pilot_ip", await hash(clientIp(request), salt + day), day, 3))
    || !(await take(db, "pilot_email", await hash(v.p.email, salt), 0, 1))) {
    return { ok: true, already: true };
  }
  const p = v.p;
  await db.prepare("INSERT INTO pilots (ts, email, nombre, despacho, programa, clientes, telefono, mensaje, origen) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)")
    .bind(Math.floor(Date.now() / 1000), p.email, p.nombre, p.despacho, p.programa, p.clientes, p.telefono, p.mensaje, p.origen).run();
  return { ok: true, notified: await notify(env, p) };
}
