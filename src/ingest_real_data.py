"""Ingesta de datos REALES del Mundial 2026 desde openfootball (CC0).

Descarga (si faltan) y parsea los archivos Football.TXT del dataset
``openfootball/worldcup`` -> ``2026--canada-usa-mexico`` y crea
``data/worldcup_real.db`` con la tabla ``matches_real``: los 104 partidos
reales (grupos A-L, octavos, cuartos, semis, 3er lugar y final).

La base principal (``data/worldcup.db``) queda intacta; ambas conviven y se
etiquetan por separado (ver README). Este script solo escribe en
``data/worldcup_real.db``.

Fuente  : https://github.com/openfootball/worldcup/tree/master/2026--canada-usa-mexico
Licencia: CC0-1.0 (https://github.com/openfootball/worldcup/blob/master/LICENSE.md)

Uso     : python src/ingest_real_data.py [--refresh] [--dest DIR] [--db FILE]
"""

import argparse
import hashlib
import re
import sqlite3
import urllib.request
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOURCE_DIR = BASE / "data" / "openfootball"
DB_PATH = BASE / "data" / "worldcup_real.db"

# Commit verificado vía GitHub API el 2026-10-19 que toca 2026--canada-usa-mexico.
# Fijado para que la ingesta sea reproducible (raw.githubusercontent no mueve master).
UPSTREAM_REPO = "openfootball/worldcup"
UPSTREAM_REF = "4b8415d5574cfa1b2531c7affa3e595ceed5d0b2"
UPSTREAM_PATH = "2026--canada-usa-mexico"
RAW_BASE = (
    f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{UPSTREAM_REF}/{UPSTREAM_PATH}"
)
SOURCE_URL = f"https://github.com/{UPSTREAM_REPO}/tree/{UPSTREAM_REF}/{UPSTREAM_PATH}"
LICENSE_NAME = "CC0-1.0"
LICENSE_URL = f"https://github.com/{UPSTREAM_REPO}/blob/{UPSTREAM_REF}/LICENSE.md"

FILES = ("cup.txt", "cup_finals.txt")
TOURNAMENT_YEAR = 2026

# Vocabulario de fases alineado con data/worldcup.db (base principal) para poder comparar.
STAGE_MAP = {
    "Round of 32": "Round of 32",
    "Round of 16": "Round of 16",
    "Quarter-final": "Quarterfinal",
    "Semi-final": "Semifinal",
    "Match for third place": "Third Place",
    "Final": "Final",
}
GROUP_HEADER_RE = re.compile(r"▪\s*Group ([A-L])\s*$")
DATE_RE = re.compile(r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+([A-Za-z]+)\s+(\d{1,2})$")
GROUP_MATCH_RE = re.compile(
    r"^\s+(?P<time>\d{1,2}:\d{2})\s+UTC(?P<off>[+-]\d+)\s+"
    r"(?P<home>.+?)\s+(?P<score>\d+-\d+)\s+\((?P<paren>[^)]*)\)\s+"
    r"(?P<away>.+?)\s+@\s+(?P<venue>.+?)\s*$"
)
FINALS_MATCH_RE = re.compile(
    r"^\s+(?:\((?P<no>\d+)\)\s+)?(?P<time>\d{1,2}:\d{2})\s+UTC(?P<off>[+-]\d+)\s+"
    r"(?P<home>.+?)\s+(?P<score>\d+-\d+)(?P<aet>\s+a\.e\.t\.)?\s+\((?P<paren>[^)]*)\)"
    r"(?:,\s*(?P<ph>\d+)-(?P<pa>\d+)\s*pen\.)?\s+"
    r"(?P<away>.+?)\s+@\s+(?P<venue>.+?)(?:\s+##.*)?\s*$"
)


class ParseError(ValueError):
    """Línea del dataset que no cumple el formato Football.TXT esperado."""


def _score_pair(text: str) -> tuple[int, int]:
    home, away = text.split("-")
    return int(home), int(away)


_MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


def _date_from(month_name: str, day: str) -> str:
    # Acepta nombres completos ("June") y abreviados ("Jun").
    prefix = month_name.lower()
    candidates = [i + 1 for i, m in enumerate(_MONTHS) if m.startswith(prefix)]
    if len(candidates) != 1:
        raise ParseError(f"Mes desconocido: {month_name!r}")
    return f"{TOURNAMENT_YEAR}-{candidates[0]:02d}-{int(day):02d}"


def _base_row(**kwargs) -> dict:
    row = {
        "match_no": None,
        "stage": None,
        "group_letter": None,
        "date": None,
        "time_local": None,
        "utc_offset": None,
        "home_team": None,
        "away_team": None,
        "home_score": None,
        "away_score": None,
        "score_90_home": None,
        "score_90_away": None,
        "ht_home": None,
        "ht_away": None,
        "pens_home": None,
        "pens_away": None,
        "extra_time": 0,
        "venue": None,
    }
    row.update(kwargs)
    return row


def parse_cup(text: str) -> list[dict]:
    """Parsea cup.txt (fase de grupos): 72 partidos de los grupos A-L."""
    rows: list[dict] = []
    group: str | None = None
    match_date: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        head = line.strip()
        g = GROUP_HEADER_RE.match(head)
        if g:
            group = g.group(1)
            continue
        d = DATE_RE.match(head)
        if d:
            match_date = _date_from(d.group(1), d.group(2))
            continue
        m = GROUP_MATCH_RE.match(line)
        if not m:
            continue
        if group is None or match_date is None:
            raise ParseError(f"Partido fuera de sección de grupo: {line!r}")
        home_score, away_score = _score_pair(m.group("score"))
        ht_home, ht_away = _score_pair(m.group("paren"))
        rows.append(
            _base_row(
                stage="Group Stage",
                group_letter=group,
                date=match_date,
                time_local=m.group("time"),
                utc_offset=m.group("off"),
                home_team=m.group("home").strip(),
                away_team=m.group("away").strip(),
                home_score=home_score,
                away_score=away_score,
                score_90_home=home_score,
                score_90_away=away_score,
                ht_home=ht_home,
                ht_away=ht_away,
                venue=m.group("venue").strip(),
            )
        )
    return rows


def parse_finals(text: str) -> list[dict]:
    """Parsea cup_finals.txt: R32, R16, cuartos, semis, 3er lugar y final (32 partidos).

    Convención openfootball de los paréntesis (verificada contra la final 2022 en
    openfootball.github.io/spec): partido regular ``X-Y (HT)``; con prórroga
    ``X-Y a.e.t. (marcador_90', HT), pen``.
    """
    rows: list[dict] = []
    stage: str | None = None
    match_date: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        head = line.strip()
        if line and not line[0].isspace():
            for keyword, label in STAGE_MAP.items():
                if keyword in head:
                    stage = label
                    break
            d = DATE_RE.match(head)
            if d:
                match_date = _date_from(d.group(1), d.group(2))
            continue
        m = FINALS_MATCH_RE.match(line)
        if not m:
            continue
        if stage is None or match_date is None:
            raise ParseError(f"Partido fuera de sección de fase: {line!r}")
        home_score, away_score = _score_pair(m.group("score"))
        paren = [
            tuple(map(int, pair.split("-"))) for pair in m.group("paren").split(",")
        ]
        extra_time = 1 if m.group("aet") else 0
        if extra_time:
            score_90 = paren[0]
            ht = paren[1] if len(paren) > 1 else (None, None)
        else:
            score_90 = (home_score, away_score)
            ht = paren[0] if paren else (None, None)
        rows.append(
            _base_row(
                match_no=int(m.group("no")) if m.group("no") else None,
                stage=stage,
                date=match_date,
                time_local=m.group("time"),
                utc_offset=m.group("off"),
                home_team=m.group("home").strip(),
                away_team=m.group("away").strip(),
                home_score=home_score,
                away_score=away_score,
                score_90_home=score_90[0],
                score_90_away=score_90[1],
                ht_home=ht[0],
                ht_away=ht[1],
                pens_home=int(m.group("ph")) if m.group("ph") else None,
                pens_away=int(m.group("pa")) if m.group("pa") else None,
                extra_time=extra_time,
                venue=m.group("venue").strip(),
            )
        )
    return rows


def validate_rows(rows: list[dict]) -> dict:
    """Comprueba invariantes del dataset real. Devuelve resumen; lanza ValueError si algo falla."""
    errors: list[str] = []
    if len(rows) != 104:
        errors.append(f"esperados 104 partidos, hay {len(rows)}")

    by_stage: dict[str, int] = {}
    for r in rows:
        by_stage[r["stage"]] = by_stage.get(r["stage"], 0) + 1
    expected = {
        "Group Stage": 72,
        "Round of 32": 16,
        "Round of 16": 8,
        "Quarterfinal": 4,
        "Semifinal": 2,
        "Third Place": 1,
        "Final": 1,
    }
    if by_stage != expected:
        errors.append(f"reparto por fase inesperado: {by_stage}")

    for letter in "ABCDEFGHIJKL":
        n = sum(1 for r in rows if r["group_letter"] == letter)
        if n != 6:
            errors.append(f"grupo {letter}: {n} partidos (esperados 6)")

    for r in rows:
        if r["stage"] == "Group Stage":
            if r["pens_home"] is not None or r["extra_time"]:
                errors.append(f"grupo con penales/prórroga: {r}")
        else:
            if r["group_letter"] is not None:
                errors.append(f"eliminatoria con grupo: {r}")
        if r["home_score"] is None or r["away_score"] is None:
            errors.append(f"partido sin marcador: {r}")
        if r["date"] is None or not ("2026-06-11" <= r["date"] <= "2026-07-19"):
            errors.append(f"fecha fuera del torneo: {r['date']}")

    dates = sorted({r["date"] for r in rows})
    if dates and (dates[0] != "2026-06-11" or dates[-1] != "2026-07-19"):
        errors.append(f"rango de fechas inesperado: {dates[0]}..{dates[-1]}")

    finals = [r for r in rows if r["stage"] == "Final"]
    third = [r for r in rows if r["stage"] == "Third Place"]
    if len(finals) == 1:
        f = finals[0]
        if (f["home_team"], f["away_team"], f["home_score"], f["away_score"]) != (
            "Spain",
            "Argentina",
            1,
            0,
        ):
            errors.append(f"final inesperada: {f}")
    if len(third) == 1:
        t = third[0]
        if (t["home_team"], t["away_team"], t["home_score"], t["away_score"]) != (
            "France",
            "England",
            4,
            6,
        ):
            errors.append(f"partido 3er lugar inesperado: {t}")

    if errors:
        raise ValueError("Dataset inconsistente: " + "; ".join(errors))

    return {
        "matches": len(rows),
        "by_stage": by_stage,
        "goals": sum(r["home_score"] + r["away_score"] for r in rows),
        "first_date": dates[0],
        "last_date": dates[-1],
    }


def download(dest_dir: Path = SOURCE_DIR, refresh: bool = False) -> list[Path]:
    """Descarga los archivos del dataset si no existen (o con --refresh)."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in FILES:
        target = dest_dir / name
        if target.exists() and not refresh:
            paths.append(target)
            continue
        url = f"{RAW_BASE}/{name}"
        print(f"[INGEST] descargando {url}")
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()
        target.write_bytes(data)
        paths.append(target)
    return paths


def _sha256_lf(text: str) -> str:
    """sha256 del contenido con finales LF (estable entre Windows/Linux)."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_db(
    rows: list[dict], db_path: Path = DB_PATH, source_files: dict | None = None
) -> dict:
    """(Re)escribe data/worldcup_real.db con matches_real + meta de procedencia."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            DROP TABLE IF EXISTS matches_real;
            DROP TABLE IF EXISTS meta;
            CREATE TABLE matches_real (
                id INTEGER PRIMARY KEY,
                match_no INTEGER,
                stage TEXT NOT NULL,
                group_letter TEXT,
                date TEXT NOT NULL,
                time_local TEXT,
                utc_offset TEXT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER NOT NULL,
                away_score INTEGER NOT NULL,
                score_90_home INTEGER,
                score_90_away INTEGER,
                ht_home INTEGER,
                ht_away INTEGER,
                pens_home INTEGER,
                pens_away INTEGER,
                extra_time INTEGER NOT NULL DEFAULT 0,
                venue TEXT
            );
            CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
            """
        )
        conn.executemany(
            """
            INSERT INTO matches_real (
                match_no, stage, group_letter, date, time_local, utc_offset,
                home_team, away_team, home_score, away_score,
                score_90_home, score_90_away, ht_home, ht_away,
                pens_home, pens_away, extra_time, venue
            ) VALUES (
                :match_no, :stage, :group_letter, :date, :time_local, :utc_offset,
                :home_team, :away_team, :home_score, :away_score,
                :score_90_home, :score_90_away, :ht_home, :ht_away,
                :pens_home, :pens_away, :extra_time, :venue
            )
            """,
            rows,
        )
        meta = {
            "source": SOURCE_URL,
            "source_ref": UPSTREAM_REF,
            "license": LICENSE_NAME,
            "license_url": LICENSE_URL,
            "accessed_on": date.today().isoformat(),
            "dataset_kind": "REAL (resultados del torneo disputado junio-julio 2026)",
            "matches": str(len(rows)),
        }
        for name, text in (source_files or {}).items():
            meta[f"sha256_{name}"] = _sha256_lf(text)
        conn.executemany("INSERT INTO meta (k, v) VALUES (?, ?)", sorted(meta.items()))
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM matches_real").fetchone()[0]
    finally:
        conn.close()
    return {"db": str(db_path), "matches": count, "meta": meta}


def load_source_texts(
    dest_dir: Path = SOURCE_DIR, refresh: bool = False
) -> dict[str, str]:
    """Asegura los archivos en disco y devuelve sus textos UTF-8."""
    paths = download(dest_dir, refresh=refresh)
    return {p.name: p.read_text(encoding="utf-8") for p in paths}


def ingest(
    dest_dir: Path = SOURCE_DIR, db_path: Path = DB_PATH, refresh: bool = False
) -> dict:
    """Pipeline completo: descarga -> parse -> valida -> escribe la DB real."""
    texts = load_source_texts(dest_dir, refresh=refresh)
    rows = parse_cup(texts["cup.txt"]) + parse_finals(texts["cup_finals.txt"])
    summary = validate_rows(rows)
    result = build_db(rows, db_path=db_path, source_files=texts)
    result["summary"] = summary
    return result


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dest", type=Path, default=SOURCE_DIR, help="directorio de los .txt"
    )
    parser.add_argument("--db", type=Path, default=DB_PATH, help="DB real de salida")
    parser.add_argument(
        "--refresh", action="store_true", help="redescarga aunque existan"
    )
    args = parser.parse_args(argv)
    result = ingest(dest_dir=args.dest, db_path=args.db, refresh=args.refresh)
    print(f"[INGEST] {result['matches']} partidos reales -> {result['db']}")
    print(
        f"[INGEST] goles: {result['summary']['goals']} | "
        f"{result['summary']['first_date']}..{result['summary']['last_date']}"
    )
    return result


if __name__ == "__main__":
    main()
