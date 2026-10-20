"""Tests para la ingesta de datos reales 2026 (openfootball, CC0)."""

import shutil
import sqlite3

import pytest

from src.ingest_real_data import (
    SOURCE_DIR,
    build_db,
    download,
    ingest,
    parse_cup,
    parse_finals,
    validate_rows,
)


def _load_texts() -> dict:
    return {
        name: (SOURCE_DIR / name).read_text(encoding="utf-8")
        for name in ("cup.txt", "cup_finals.txt")
    }


@pytest.fixture(scope="module")
def rows():
    texts = _load_texts()
    return parse_cup(texts["cup.txt"]) + parse_finals(texts["cup_finals.txt"])


def test_dataset_has_104_real_matches(rows):
    summary = validate_rows(rows)
    assert summary["matches"] == 104
    assert summary["by_stage"] == {
        "Group Stage": 72,
        "Round of 32": 16,
        "Round of 16": 8,
        "Quarterfinal": 4,
        "Semifinal": 2,
        "Third Place": 1,
        "Final": 1,
    }
    assert summary["first_date"] == "2026-06-11"
    assert summary["last_date"] == "2026-07-19"
    assert summary["goals"] == 308


def test_real_final_and_third_place(rows):
    final = next(r for r in rows if r["stage"] == "Final")
    assert (final["home_team"], final["away_team"]) == ("Spain", "Argentina")
    assert (final["home_score"], final["away_score"]) == (1, 0)
    assert final["extra_time"] == 1
    assert (final["score_90_home"], final["score_90_away"]) == (0, 0)
    assert (final["ht_home"], final["ht_away"]) == (0, 0)
    assert final["date"] == "2026-07-19"
    assert final["match_no"] == 104

    third = next(r for r in rows if r["stage"] == "Third Place")
    assert (third["home_team"], third["away_team"]) == ("France", "England")
    assert (third["home_score"], third["away_score"]) == (4, 6)
    assert (third["ht_home"], third["ht_away"]) == (0, 4)
    assert third["date"] == "2026-07-18"


def test_group_stage_shape(rows):
    groups = [r for r in rows if r["stage"] == "Group Stage"]
    assert len(groups) == 72
    for letter in "ABCDEFGHIJKL":
        assert sum(1 for r in groups if r["group_letter"] == letter) == 6
    assert all(r["ht_home"] is not None for r in groups)
    assert all(r["pens_home"] is None and not r["extra_time"] for r in groups)


def test_knockout_match_numbers(rows):
    knockout = [r for r in rows if r["stage"] != "Group Stage"]
    assert sorted(r["match_no"] for r in knockout) == list(range(73, 105))
    assert all(r["group_letter"] is None for r in knockout)


def test_penalties_only_in_knockout(rows):
    pens = [r for r in rows if r["pens_home"] is not None]
    assert len(pens) == 4
    assert all(r["stage"] != "Group Stage" for r in pens)
    for r in pens:
        assert r["pens_home"] != r["pens_away"]
        assert r["extra_time"] == 1


def test_validate_rejects_tampered_dataset(rows):
    with pytest.raises(ValueError):
        validate_rows(rows[:-1])
    tampered = [dict(r) for r in rows]
    final = next(r for r in tampered if r["stage"] == "Final")
    final["home_score"] = 2
    with pytest.raises(ValueError):
        validate_rows(tampered)


def test_build_db_roundtrip(tmp_path, rows):
    texts = _load_texts()
    db_path = tmp_path / "worldcup_real.db"
    result = build_db(rows, db_path=db_path, source_files=texts)

    assert result["matches"] == 104
    assert result["meta"]["license"] == "CC0-1.0"
    assert "openfootball/worldcup" in result["meta"]["source"]
    assert result["meta"]["sha256_cup.txt"]

    conn = sqlite3.connect(str(db_path))
    try:
        count = conn.execute("SELECT COUNT(*) FROM matches_real").fetchone()[0]
        assert count == 104
        final = conn.execute(
            "SELECT home_team, away_team, home_score, away_score, extra_time "
            "FROM matches_real WHERE stage = 'Final'"
        ).fetchone()
        assert final == ("Spain", "Argentina", 1, 0, 1)
        goals = conn.execute(
            "SELECT SUM(home_score + away_score) FROM matches_real"
        ).fetchone()[0]
        assert goals == 308
    finally:
        conn.close()


def test_download_reuses_local_files(tmp_path):
    dest = tmp_path / "openfootball"
    dest.mkdir()
    for name in ("cup.txt", "cup_finals.txt"):
        shutil.copy(SOURCE_DIR / name, dest / name)
    paths = download(dest_dir=dest, refresh=False)
    assert [p.name for p in paths] == ["cup.txt", "cup_finals.txt"]
    assert all(p.exists() for p in paths)


def test_ingest_offline_pipeline(tmp_path):
    dest = tmp_path / "openfootball"
    dest.mkdir()
    for name in ("cup.txt", "cup_finals.txt"):
        shutil.copy(SOURCE_DIR / name, dest / name)
    db_path = tmp_path / "worldcup_real.db"
    result = ingest(dest_dir=dest, db_path=db_path, refresh=False)
    assert result["matches"] == 104
    assert result["summary"]["goals"] == 308
    assert db_path.exists()
