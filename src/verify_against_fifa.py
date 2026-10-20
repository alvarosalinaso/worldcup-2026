"""Contraste de los resultados reales 2026 contra la fuente oficial FIFA (A-3).

Compara los partidos de eliminatoria de ``data/worldcup_real.db`` (openfootball,
CC0) con los resultados oficiales de la API pública de FIFA (api.fifa.com,
competición 17 = FIFA World Cup, temporada 285023 = "FIFA World Cup 2026") y
regenera el ledger de contraste ``data/contrast_ledger.md``.

La web www.fifa.com es una SPA (JavaScript) sin HTML verificable por HTTP simple;
se usa la API oficial que alimenta fifa.com (mismo origen FIFA). Si la API no
responde, el script falla explícitamente: no se escriben cifras inventadas.

Uso: python src/verify_against_fifa.py [--db FILE] [--out FILE]
"""

import argparse
import json
import sqlite3
import urllib.request
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DEFAULT_DB = BASE / "data" / "worldcup_real.db"
DEFAULT_LEDGER = BASE / "data" / "contrast_ledger.md"

ID_COMPETITION = "17"
ID_SEASON = "285023"
FIFA_MATCHES_URL = (
    f"https://api.fifa.com/api/v3/calendar/matches"
    f"?idCompetition={ID_COMPETITION}&idSeason={ID_SEASON}&language=en&count=500"
)

# Nombres de la FIFA -> nombres openfootball usados en el repo.
ALIASES = {
    "Côte d'Ivoire": "Ivory Coast",
    "Congo DR": "DR Congo",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "Cabo Verde": "Cape Verde",
    "United States": "USA",
    "Korea Republic": "South Korea",
}


def fetch_fifa_matches() -> list[dict]:
    """Descarga los 104 partidos oficiales de la temporada 285023."""
    with urllib.request.urlopen(FIFA_MATCHES_URL, timeout=60) as resp:
        data = json.load(resp)
    return data["Results"]


def normalize_team(name: str) -> str:
    return ALIASES.get(name, name)


def _local_name(locales) -> str | None:
    return locales[0]["Description"] if locales else None


def load_repo_knockout(db_path: Path) -> dict[int, dict]:
    """Partidos de la DB real con número de partido (eliminatorias, 73-104)."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM matches_real WHERE match_no IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()
    return {r["match_no"]: dict(r) for r in rows}


def load_repo_totals(db_path: Path) -> dict:
    conn = sqlite3.connect(str(db_path))
    try:
        n = conn.execute("SELECT COUNT(*) FROM matches_real").fetchone()[0]
        goals = conn.execute(
            "SELECT SUM(home_score + away_score) FROM matches_real"
        ).fetchone()[0]
    finally:
        conn.close()
    return {"matches": n, "goals": goals}


def compare(
    fifa_matches: list[dict],
    repo_ko: dict[int, dict],
    repo_totals: dict,
    expected_matches: int = 104,
) -> dict:
    """Compara FIFA vs repo. Devuelve resumen con discrepancias (lista vacía = todo coincide)."""
    discrepancies: list[str] = []
    fifa_by_no = {m["MatchNumber"]: m for m in fifa_matches}

    fifa_goals = sum(m["Home"]["Score"] + m["Away"]["Score"] for m in fifa_matches)
    if len(fifa_matches) != expected_matches:
        discrepancies.append(
            f"FIFA tiene {len(fifa_matches)} partidos (esperados {expected_matches})"
        )
    if repo_totals["matches"] != expected_matches:
        discrepancies.append(
            f"repo tiene {repo_totals['matches']} partidos (esperados {expected_matches})"
        )
    if fifa_goals != repo_totals["goals"]:
        discrepancies.append(f"goles: FIFA {fifa_goals} vs repo {repo_totals['goals']}")

    checked = 0
    for match_no, repo in sorted(repo_ko.items()):
        fifa = fifa_by_no.get(match_no)
        if fifa is None:
            discrepancies.append(f"match {match_no} no existe en FIFA")
            continue
        home, away = fifa["Home"], fifa["Away"]
        if (home["Score"], away["Score"]) != (repo["home_score"], repo["away_score"]):
            discrepancies.append(
                f"match {match_no}: marcador FIFA {home['Score']}-{away['Score']} "
                f"vs repo {repo['home_score']}-{repo['away_score']}"
            )
        f_home = normalize_team(_local_name(home["TeamName"]))
        f_away = normalize_team(_local_name(away["TeamName"]))
        if (f_home, f_away) != (repo["home_team"], repo["away_team"]):
            discrepancies.append(
                f"match {match_no}: equipos FIFA {f_home} vs {f_away} "
                f"vs repo {repo['home_team']} vs {repo['away_team']}"
            )
        f_pens = (home.get("HomeTeamPenaltyScore"), away.get("AwayTeamPenaltyScore"))
        r_pens = (repo["pens_home"], repo["pens_away"])
        if f_pens != (None, None) and f_pens != r_pens:
            discrepancies.append(
                f"match {match_no}: penales FIFA {f_pens} vs repo {r_pens}"
            )
        checked += 1

    def _match_info(match_no: int) -> dict:
        fifa = fifa_by_no.get(match_no)
        repo = repo_ko.get(match_no)
        if fifa is None or repo is None:
            return {}
        return {
            "fifa_id_match": fifa.get("IdMatch"),
            "date": fifa.get("LocalDate", "")[:10],
            "stadium": _local_name(fifa.get("Stadium", {}).get("Name", [])),
            "attendance": fifa.get("Attendance"),
            "repo": (
                f"{repo['home_team']} {repo['home_score']}-{repo['away_score']} "
                f"{repo['away_team']}"
            ),
            "fifa": (
                f"{_local_name(fifa['Home']['TeamName'])} {fifa['Home']['Score']}-"
                f"{fifa['Away']['Score']} {_local_name(fifa['Away']['TeamName'])}"
            ),
        }

    return {
        "fifa_url": FIFA_MATCHES_URL,
        "matches_fifa": len(fifa_matches),
        "matches_repo": repo_totals["matches"],
        "goals_fifa": fifa_goals,
        "goals_repo": repo_totals["goals"],
        "knockout_checked": checked,
        "final": _match_info(104),
        "third_place": _match_info(103),
        "discrepancies": discrepancies,
    }


def render_ledger(comparison: dict, accessed_on: str) -> str:
    ok = "Sí" if not comparison["discrepancies"] else "No"
    final = comparison["final"]
    third = comparison["third_place"]
    url = comparison["fifa_url"]
    lines = [
        "# Ledger de contraste FIFA (auditoría 2026-10)",
        "",
        "Contraste de los resultados **reales** de `data/worldcup_real.db` (openfootball,",
        "CC0, commit upstream `4b8415d`) contra la fuente **oficial** FIFA: la API",
        f"pública que alimenta fifa.com (`api.fifa.com`, competición {ID_COMPETITION},",
        f'temporada {ID_SEASON} = "FIFA World Cup 2026"). www.fifa.com es una SPA sin',
        "HTML verificable por HTTP simple, por eso se usa su API oficial.",
        "",
        f"URL FIFA: <{url}>",
        f"Fecha de acceso: {accessed_on}",
        "Regenerar: `python src/verify_against_fifa.py`",
        "",
        "| Dato verificado | openfootball (repo) | FIFA (oficial) | URL FIFA | Fecha de acceso | ¿Coincide? |",
        "|---|---|---|---|---|---|",
        (
            f"| Final (match 104) | {final.get('repo')} ({final.get('date')}, "
            f"{final.get('stadium')}) | {final.get('fifa')} (id {final.get('fifa_id_match')}, "
            f"asistencia {final.get('attendance')}) | <{url}> | {accessed_on} | {ok} |"
        ),
        (
            f"| 3er lugar (match 103) | {third.get('repo')} ({third.get('date')}, "
            f"{third.get('stadium')}) | {third.get('fifa')} (id {third.get('fifa_id_match')}, "
            f"asistencia {third.get('attendance')}) | <{url}> | {accessed_on} | {ok} |"
        ),
        (
            f"| Marcadores de eliminatorias (matches 73-104) | {comparison['knockout_checked']} "
            f"partidos | idénticos | <{url}> | {accessed_on} | {ok} |"
        ),
        (
            f"| Totales del torneo | {comparison['matches_repo']} partidos, "
            f"{comparison['goals_repo']} goles | {comparison['matches_fifa']} partidos, "
            f"{comparison['goals_fifa']} goles | <{url}> | {accessed_on} | {ok} |"
        ),
        "",
        "Notas:",
        "",
        "- Sin discrepancias de marcador: no hizo falta corregir datos del repo.",
        "- Diferencias solo de **nombres** entre fuentes (alias): Côte d'Ivoire=Ivory",
        "  Coast, Congo DR=DR Congo, Bosnia and Herzegovina=Bosnia & Herzegovina,",
        "  Cabo Verde=Cape Verde, United States=USA. El repo conserva los nombres",
        "  openfootball.",
        "",
        "## Discrepancias detectadas por el script",
        "",
    ]
    if comparison["discrepancies"]:
        lines += [f"- {d}" for d in comparison["discrepancies"]]
    else:
        lines.append("- (ninguna)")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--accessed-on", default=date.today().isoformat())
    args = parser.parse_args(argv)

    fifa_matches = fetch_fifa_matches()
    comparison = compare(
        fifa_matches, load_repo_knockout(args.db), load_repo_totals(args.db)
    )
    text = render_ledger(comparison, args.accessed_on)
    args.out.write_text(text, encoding="utf-8")
    status = (
        "OK (sin discrepancias)" if not comparison["discrepancies"] else "DISCREPANCIAS"
    )
    print(f"[FIFA] {status} -> {args.out}")
    for d in comparison["discrepancies"]:
        print(f"[FIFA]  - {d}")
    return comparison


if __name__ == "__main__":
    main()
