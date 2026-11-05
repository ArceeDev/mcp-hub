-- Uso por llamada a herramienta. lic es un hash SHA-256 truncado de la licencia; nunca se guarda la licencia ni el contenido.
CREATE TABLE IF NOT EXISTS usage (
  id INTEGER PRIMARY KEY,
  lic TEXT NOT NULL,
  ts INTEGER NOT NULL,
  slug TEXT NOT NULL,
  tool TEXT NOT NULL,
  ok INTEGER NOT NULL,
  credits INTEGER NOT NULL DEFAULT 0,
  ms INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS usage_lic_ts ON usage (lic, ts);
CREATE INDEX IF NOT EXISTS usage_ts ON usage (ts);
