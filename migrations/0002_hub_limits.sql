-- Contadores de abuso del hub: licencias de prueba y demos web. k es un hash (nunca el correo ni la IP).
-- day = días desde 1970 (UTC); 0 = para siempre (una licencia de prueba por correo).
CREATE TABLE IF NOT EXISTS hub_limits (
  kind TEXT NOT NULL,
  k TEXT NOT NULL,
  day INTEGER NOT NULL,
  n INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (kind, k, day)
);
CREATE INDEX IF NOT EXISTS hub_limits_day ON hub_limits (day);
