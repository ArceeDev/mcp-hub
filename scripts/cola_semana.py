"""Cola de publicaciones de marketing (marketing/cola.json).

  python scripts/cola_semana.py --check            valida la cola (longitud en X, UTM, fechas, estados)
  python scripts/cola_semana.py --semana [FECHA]   Markdown con lo de los 7 días desde FECHA (lunes por defecto)

La GitHub Action «cola-marketing» abre cada lunes un issue con la semana para que Arcee apruebe los textos.
Nada se publica solo: X se programa tras la aprobación (vidIQ) y LinkedIn con su programador nativo.
Reddit y Hacker News quedan fuera de la cola: sus normas exigen publicar a mano y participar.
"""
import datetime as dt
import json
import pathlib
import re
import sys

COLA = pathlib.Path(__file__).resolve().parent.parent / "marketing" / "cola.json"
X_MAX, URL_LEN = 280, 23  # X cuenta cada enlace como 23 caracteres
ESTADOS = {"pendiente", "aprobado", "programado", "publicado", "descartado"}
CANALES = {"x", "linkedin"}


def x_len(texto: str, url: str) -> int:
    return len(re.sub(r"https?://\S+", "x" * URL_LEN, texto)) + (1 + URL_LEN if url else 0)


def check(items) -> list:
    errs, ids, prev = [], set(), ""
    for it in items:
        i = it.get("id", "?")
        if i in ids:
            errs.append(f"{i}: id repetido")
        ids.add(i)
        if it.get("canal") not in CANALES:
            errs.append(f"{i}: canal no permitido (solo x y linkedin; Reddit/HN a mano)")
        if it.get("estado") not in ESTADOS:
            errs.append(f"{i}: estado desconocido")
        try:
            dt.datetime.fromisoformat(it["fecha"])
        except Exception:
            errs.append(f"{i}: fecha no ISO 8601 con zona")
        if it.get("fecha", "") < prev:
            errs.append(f"{i}: fuera de orden")
        prev = it.get("fecha", "")
        url = it.get("url", "")
        if url and "utm_source=" not in url:
            errs.append(f"{i}: url sin UTM")
        if it.get("canal") == "x" and x_len(it.get("texto", ""), url) > X_MAX:
            errs.append(f"{i}: {x_len(it['texto'], url)} caracteres en X (máx. {X_MAX})")
        if it.get("canal") == "linkedin" and len(it.get("texto", "")) > 2800:
            errs.append(f"{i}: demasiado largo para LinkedIn")
    return errs


def semana(items, desde: dt.date) -> str:
    hasta = desde + dt.timedelta(days=7)
    sel = [it for it in items if desde <= dt.date.fromisoformat(it["fecha"][:10]) < hasta and it["estado"] in ("pendiente", "aprobado")]
    out = [f"Publicaciones del {desde} al {hasta - dt.timedelta(days=1)}. Marca las que apruebas y escribe en el hilo de Claude «aprueba la cola»: se programan X (vidIQ) y te paso LinkedIn para su programador.", ""]
    if not sel:
        out.append("No hay publicaciones en cola esta semana: pide a Claude que genere la siguiente tanda.")
    for it in sel:
        out += [f"- [ ] **{it['fecha'][:16].replace('T', ' ')} · {it['canal']} · {it['idioma']}** `{it['id']}`", "",
                "  " + it["texto"].replace("\n", "\n  "), "", f"  {it['url']}", ""]
    return "\n".join(out)


def main(argv):
    items = json.loads(COLA.read_text(encoding="utf-8"))
    if "--check" in argv:
        errs = check(items)
        print("\n".join(errs) or f"OK: {len(items)} publicaciones")
        return 1 if errs else 0
    if "--semana" in argv:
        rest = argv[argv.index("--semana") + 1:]
        d = dt.date.fromisoformat(rest[0]) if rest else dt.date.today()
        print(semana(items, d - dt.timedelta(days=d.weekday())))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
