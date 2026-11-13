-- Visitas agregadas del hub (RGPD): sin cookies, sin IP, sin user-agent, sin identificadores.
-- Una fila por día y combinación (página, origen, UTM, país, entrada); n = páginas vistas.
CREATE TABLE IF NOT EXISTS visits (
  day INTEGER NOT NULL,           -- días desde 1970 (UTC)
  path TEXT NOT NULL,             -- solo la ruta, nunca la query
  ref TEXT NOT NULL,              -- solo el dominio de origen ('' = directo o interno)
  src TEXT NOT NULL,              -- utm_source
  med TEXT NOT NULL,              -- utm_medium
  camp TEXT NOT NULL,             -- utm_campaign
  country TEXT NOT NULL,          -- ISO-2 de Cloudflare (request.cf.country)
  entry INTEGER NOT NULL,         -- 1 = primera página de la visita (llega de fuera o directo)
  dev TEXT NOT NULL DEFAULT '',   -- m = móvil, d = escritorio (deducido del user-agent, que no se guarda)
  asn INTEGER NOT NULL DEFAULT 0, -- red de origen (request.cf.asn): separa centros de datos de operadores domésticos
  n INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, path, ref, src, med, camp, country, entry, dev, asn)
);
