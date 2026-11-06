// Contadores en D1 (tabla hub_limits) para la prueba gratis y las demos. Atómicos: un solo UPSERT condicional.

export const today = (now = Date.now()) => Math.floor(now / 86_400_000);

export async function hash(value, salt = "") {
  const data = new TextEncoder().encode(salt + "\u0000" + String(value).trim().toLowerCase());
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", data));
  return Array.from(d.slice(0, 16), (b) => b.toString(16).padStart(2, "0")).join("");
}

// Suma 1 si el contador no ha llegado a max. Devuelve true si se ha sumado (dentro del límite).
export async function take(db, kind, k, day, max) {
  if (max <= 0) return false;
  const row = await db.prepare(
    "INSERT INTO hub_limits (kind, k, day, n) VALUES (?1, ?2, ?3, 1) " +
    "ON CONFLICT (kind, k, day) DO UPDATE SET n = n + 1 WHERE n < ?4 RETURNING n",
  ).bind(kind, k, day, max).first();
  return !!row;
}

// Devuelve una unidad (la operación falló después de contar y no debe gastar el cupo del usuario).
export async function giveBack(db, kind, k, day) {
  await db.prepare("UPDATE hub_limits SET n = n - 1 WHERE kind = ?1 AND k = ?2 AND day = ?3 AND n > 0")
    .bind(kind, k, day).run();
}

export function clientIp(request) {
  return request.headers.get("cf-connecting-ip") || "unknown";
}

export function num(v, dflt) {
  const n = Number.parseInt(v, 10);
  return Number.isFinite(n) && n >= 0 ? n : dflt;
}
