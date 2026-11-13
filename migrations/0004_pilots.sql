-- Solicitudes de piloto de despachos (/piloto/). Datos que el propio despacho envía para que le contactemos (RGPD art. 6.1.b).
-- Se borran a los 12 meses si no hay relación comercial (ver /confianza/).
CREATE TABLE IF NOT EXISTS pilots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER NOT NULL,            -- segundos UTC
  email TEXT NOT NULL,
  nombre TEXT NOT NULL,
  despacho TEXT NOT NULL,
  programa TEXT NOT NULL,         -- contasol | a3 | contaplus | sage50 | holded | excel | otro
  clientes TEXT NOT NULL,         -- tramo: 1-10 | 11-30 | 31-100 | 100+
  telefono TEXT NOT NULL DEFAULT '',
  mensaje TEXT NOT NULL DEFAULT '',
  origen TEXT NOT NULL DEFAULT '' -- utm_source o página de origen
);
CREATE INDEX IF NOT EXISTS pilots_ts ON pilots (ts);
