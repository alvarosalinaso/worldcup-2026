"""Export analytical visualizations from the World Cup 2026 database.

Generates three CSV datasets and an embed snippets markdown file for
external visualization tools (Datawrapper, Flourish, Observable).
"""

import csv
import sqlite3
from pathlib import Path
from typing import Optional

from seed_data import get_conn

EXPORT_DIR = Path(__file__).resolve().parent.parent / "data" / "export"
DB_PATH_DEFAULT = Path(__file__).resolve().parent.parent / "data" / "worldcup.db"

ROUND_ORDER: dict[str, int] = {
    "Group Stage": 1,
    "Round of 32": 2,
    "Round of 16": 3,
    "Quarterfinal": 4,
    "Semifinal": 5,
    "Third Place": 6,
    "Final": 7,
}


def _ensure_export_dir() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _write_csv(filename: str, headers: list[str], rows: list[tuple]) -> Path:
    path = EXPORT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        writer.writerows(rows)
    return path


def _stage_label(stage: int) -> str:
    labels = {
        1: "Group Stage",
        2: "Round of 32",
        3: "Round of 16",
        4: "Quarterfinal",
        5: "Semifinal",
        6: "Third Place",
        7: "Final",
    }
    return labels.get(stage, f"Stage {stage}")


def export_asistencia_sedes(conn: sqlite3.Connection) -> Path:
    """Stadium attendance summary with occupancy rate."""
    cur = conn.execute(
        """
        SELECT
            s.name          AS stadium,
            s.host_city     AS city,
            s.country       AS country,
            s.capacity      AS capacity,
            COUNT(*)        AS total_matches,
            SUM(m.attendance)  AS total_attendance,
            ROUND(AVG(m.attendance)) AS avg_attendance,
            ROUND(AVG(m.attendance * 100.0 / s.capacity), 1) AS occupancy_rate
        FROM matches m
        JOIN stadiums s ON m.stadium_id = s.stadium_id
        WHERE m.attendance IS NOT NULL
        GROUP BY s.stadium_id
        ORDER BY occupancy_rate DESC
        """
    )
    rows = cur.fetchall()
    headers = [
        "stadium",
        "city",
        "country",
        "capacity",
        "total_matches",
        "total_attendance",
        "avg_attendance",
        "occupancy_rate",
    ]
    path = _write_csv("dw_asistencia_sedes.csv", headers, rows)
    print(f"  -> {path.name} ({len(rows)} stadiums)")
    return path


def export_flourish_sankey(conn: sqlite3.Connection) -> Path:
    """Confederation progression through rounds for Sankey diagram.

    Each row represents (confederation, round_eliminated, team_count).
    A team is counted in the deepest round it reached.
    """
    cur = conn.execute(
        """
        SELECT t.team_id, t.confederation, t.name
        FROM teams t
        ORDER BY t.team_id
        """
    )
    teams = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

    cur = conn.execute(
        """
        SELECT match_id, round, stage_number,
               home_team_id, away_team_id, home_score, away_score,
               home_penalty, away_penalty
        FROM matches
        ORDER BY match_number
        """
    )
    matches = cur.fetchall()

    team_max_round: dict[int, int] = {}
    for match in matches:
        match_id, round_name, stage, h_id, a_id, hs, as_, hp, ap = match
        for tid in (h_id, a_id):
            prev = team_max_round.get(tid, 1)
            if stage > prev:
                team_max_round[tid] = stage

    conf_round: dict[tuple[str, int], int] = {}
    for tid, (conf, _) in teams.items():
        max_stage = team_max_round.get(tid, 1)
        key = (conf, max_stage)
        conf_round[key] = conf_round.get(key, 0) + 1

    conf_order = ["UEFA", "CONMEBOL", "CAF", "CONCACAF", "AFC", "OFC"]
    rows: list[tuple[str, str, int]] = []
    for conf in conf_order:
        for stage in sorted(ROUND_ORDER.values()):
            count = conf_round.get((conf, stage), 0)
            if count > 0:
                rows.append((conf, _stage_label(stage), count))

    headers = ["confederation", "round_eliminated", "teams_count"]
    path = _write_csv("flourish_sankey_avance.csv", headers, rows)
    print(f"  -> {path.name} ({len(rows)} flows)")
    return path


def export_observable_bracket(conn: sqlite3.Connection) -> Path:
    """All matches formatted for an interactive bracket visualization."""
    cur = conn.execute(
        """
        SELECT
            m.round,
            m.match_number,
            t1.name       AS home_team,
            t2.name       AS away_team,
            m.home_score,
            m.away_score,
            m.home_penalty,
            m.away_penalty,
            m.extra_time
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        ORDER BY
            CASE m.round
                WHEN 'Group Stage' THEN 1 WHEN 'Round of 32' THEN 2
                WHEN 'Round of 16' THEN 3 WHEN 'Quarterfinal' THEN 4
                WHEN 'Semifinal' THEN 5 WHEN 'Third Place' THEN 6
                WHEN 'Final' THEN 7
            END,
            m.match_number
        """
    )
    rows: list[tuple] = []
    for row in cur.fetchall():
        rnd, mnum, home, away, hs, as_, hp, ap, et = row
        home_display = home
        away_display = away
        if rnd == "Group Stage":
            winner = ""
        else:
            home_total = hs + (hp or 0)
            away_total = as_ + (ap or 0)
            if home_total > away_total:
                winner = home
            elif away_total > home_total:
                winner = away
            else:
                winner = ""
        rows.append((rnd, mnum, home_display, away_display, hs, as_, winner))

    headers = [
        "round",
        "match_number",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "winner",
    ]
    path = _write_csv("observable_bracket.csv", headers, rows)
    print(f"  -> {path.name} ({len(rows)} matches)")
    return path


def generate_embed_snippets() -> Path:
    """Generate markdown file with responsive HTML embed snippets."""
    snippet = """# Embed Snippets - FIFA World Cup 2026

Responsive HTML snippets for embedding interactive visualizations.

---

## 1. Datawrapper Map - Venue Attendance

```html
<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
  <iframe
    title="World Cup 2026 – Venue Attendance"
    src="https://datawrapper.dwcdn.net/ATTACH_YOUR_CHART_ID/"
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
    loading="lazy"
    allowfullscreen
    referrerpolicy="no-referrer-when-downgrade">
  </iframe>
</div>
```

> **Setup:** Upload `data/export/dw_asistencia_sedes.csv` to
> [Datawrapper](https://www.datawrapper.de/) and replace `ATTACH_YOUR_CHART_ID`
> with the published chart ID.

---

## 2. Flourish Sankey - Confederation Advancement

```html
<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
  <iframe
    title="World Cup 2026 – Confederation Advancement"
    src="https://flo.uri.sh/story/ATTACH_YOUR_STORY_ID/embed"
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
    loading="lazy"
    allowfullscreen
    referrerpolicy="no-referrer-when-downgrade">
  </iframe>
</div>
```

> **Setup:** Upload `data/export/flourish_sankey_avance.csv` to
> [Flourish](https://flourish.studio/) as a Sankey diagram and replace
> `ATTACH_YOUR_STORY_ID` with the published story ID.

---

## 3. Observable Interactive Bracket

```html
<div style="position:relative;padding-bottom:75%;height:0;overflow:hidden;max-width:100%;">
  <iframe
    title="World Cup 2026 – Interactive Bracket"
    src="https://observablehq.com/embed/ATTACH_YOUR_NOTEBOOK_ID?cells=chart"
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
    loading="lazy"
    allowfullscreen
    referrerpolicy="no-referrer-when-downgrade">
  </iframe>
</div>
```

> **Setup:** Publish an Observable notebook using `data/export/observable_bracket.csv`
> and replace `ATTACH_YOUR_NOTEBOOK_ID` with the published notebook ID.

---

## Quick Start

1. Run the export script:
   ```bash
   python src/export_visualizations.py
   ```
2. CSV files are generated in `data/export/`.
3. Upload each CSV to the corresponding platform.
4. Replace the placeholder IDs in the snippets above.
5. Paste the HTML into your page or README.

## Responsive Notes

- All embeds use the `padding-bottom` trick for aspect-ratio-responsive sizing.
- `max-width: 100%` prevents horizontal overflow on narrow screens.
- `loading="lazy"` defers loading until the embed scrolls into view.
- `allowfullscreen` enables fullscreen toggle on the embedded content.
"""

    path = EXPORT_DIR / "embed_snippets.md"
    path.write_text(snippet, encoding="utf-8")
    print(f"  -> {path.name}")
    return path


def main(db_path: Optional[str] = None) -> None:
    """Main export pipeline."""
    target = Path(db_path) if db_path else DB_PATH_DEFAULT

    if not target.exists():
        print(f"Database not found at {target}")
        print(
            "Run 'python src/seed_data.py' first to create and populate the database."
        )
        return

    _ensure_export_dir()
    print(f"Connecting to {target} ...")

    try:
        conn = get_conn(str(target))
    except sqlite3.Error as exc:
        print(f"Failed to connect to database: {exc}")
        return

    try:
        print("\nExporting CSV datasets:")
        export_asistencia_sedes(conn)
        export_flourish_sankey(conn)
        export_observable_bracket(conn)
        print("\nGenerating embed snippets:")
        generate_embed_snippets()
        print(f"\nAll exports written to {EXPORT_DIR}")

        # Advanced analytics
        from clustering_analysis import run_clustering

        run_clustering()

        from forecasting import run_forecasting

        run_forecasting()

        from ranking_analysis import run_ranking

        run_ranking()

        from optimization_analysis import run_optimization

        run_optimization()

        from sensitivity_analysis import run_sensitivity

        run_sensitivity()

        # Statistical tests
        from statistical_tests import run_statistical_tests

        run_statistical_tests()

        # Generate executive tables
        from generate_tables import generate as generate_exec_tables

        generate_exec_tables()

    except sqlite3.Error as exc:
        print(f"Query error: {exc}")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    database = sys.argv[1] if len(sys.argv) > 1 else None
    main(database)
