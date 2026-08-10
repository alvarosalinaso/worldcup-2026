"""Tests de seed_data y queries.py sobre una base SQLite temporal."""

import sqlite3

import pandas as pd
import pytest

import queries
import seed_data


@pytest.fixture()
def seeded_db(tmp_path):
    """Crea y puebla una base SQLite temporal, devolviendo la ruta."""
    db_path = str(tmp_path / "worldcup.db")
    seed_data.init_db(db_path)
    seed_data.seed(db_path)
    return db_path


# ── seed_data ──────────────────────────────────────────────────────────────────
def test_seed_creates_all_tables(seeded_db):
    conn = sqlite3.connect(seeded_db)
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    expected = {
        "stadiums",
        "teams",
        "groups",
        "group_standings",
        "matches",
        "goals",
        "awards",
    }
    assert expected.issubset(tables)


def test_seed_populates_expected_rows(seeded_db):
    assert len(queries.stadium_map(db_path=seeded_db)) == 16
    assert len(queries.team_performance(db_path=seeded_db)) == 48
    assert len(queries.tournament_ranking(db_path=seeded_db)) == 48


# ── group standings ────────────────────────────────────────────────────────────
def test_group_table_returns_four_rows(seeded_db):
    df = queries.group_table("A", db_path=seeded_db)
    assert len(df) == 4
    assert list(df.columns) == [
        "Pos",
        "Team",
        "Pld",
        "W",
        "D",
        "L",
        "GF",
        "GA",
        "GD",
        "Pts",
    ]


def test_group_table_sorted_by_pos(seeded_db):
    df = queries.group_table("F", db_path=seeded_db)
    assert df["Pos"].tolist() == sorted(df["Pos"].tolist())


def test_all_group_tables_has_48_teams(seeded_db):
    df = queries.all_group_tables(db_path=seeded_db)
    assert len(df) == 48
    assert df["Group"].nunique() == 12


# ── knockout ───────────────────────────────────────────────────────────────────
def test_knockout_matches_exclude_group_stage(seeded_db):
    df = queries.knockout_matches(db_path=seeded_db)
    assert not df.empty
    assert (df["round"] != "Group Stage").all()


# ── top scorers ────────────────────────────────────────────────────────────────
def test_top_scorers_mbappe_first(seeded_db):
    df = queries.top_scorers(db_path=seeded_db)
    assert df.iloc[0]["Player"] == "Kylian Mbappé"
    assert df.iloc[0]["Goals"] == 10


def test_top_scorers_respects_limit(seeded_db):
    assert len(queries.top_scorers(limit=5, db_path=seeded_db)) == 5


def test_top_scorers_sorted_descending(seeded_db):
    df = queries.top_scorers(db_path=seeded_db)
    assert df["Goals"].tolist() == sorted(df["Goals"].tolist(), reverse=True)


# ── attendance ─────────────────────────────────────────────────────────────────
def test_attendance_by_venue_has_16_stadiums(seeded_db):
    df = queries.attendance_by_venue(db_path=seeded_db)
    assert len(df) == 16
    assert set(["Stadium", "Total", "Avg"]).issubset(df.columns)


# ── matches per day / goals per round ─────────────────────────────────────────
def test_matches_per_day_not_empty(seeded_db):
    df = queries.matches_per_day(db_path=seeded_db)
    assert not df.empty
    assert list(df.columns) == ["Date", "Matches"]


def test_goals_per_round_covers_seven_rounds(seeded_db):
    df = queries.goals_per_round(db_path=seeded_db)
    assert len(df) == 7
    assert df["Goals"].sum() == 308


# ── per-team / confederation ───────────────────────────────────────────────────
def test_team_performance_has_spain_as_champion(seeded_db):
    df = queries.team_performance(db_path=seeded_db)
    spain = df[df["Team"] == "Spain"].iloc[0]
    assert spain["Wins"] >= 7


def test_goals_by_confederation_includes_six(seeded_db):
    df = queries.goals_by_confederation(db_path=seeded_db)
    assert len(df) >= 6


# ── champion path ──────────────────────────────────────────────────────────────
def test_champion_path_includes_final(seeded_db):
    df = queries.champion_path(db_path=seeded_db)
    assert not df.empty
    assert (df["Round"] == "Final").any()


# ── stadium utilization / map ──────────────────────────────────────────────────
def test_stadium_utilization_pct_between_0_and_100(seeded_db):
    df = queries.stadium_utilization(db_path=seeded_db)
    assert (df["Pct_Full"] >= 0).all()
    assert (df["Pct_Full"] <= 100).all()


def test_stadium_map_has_matches_for_used_venues(seeded_db):
    df = queries.stadium_map(db_path=seeded_db)
    assert len(df) == 16
    assert df["matches"].sum() == 104


# ── full ranking / debutants ───────────────────────────────────────────────────
def test_tournament_ranking_48_teams(seeded_db):
    df = queries.tournament_ranking(db_path=seeded_db)
    assert len(df) == 48


def test_debutants_only_debut_teams(seeded_db):
    df = queries.debutants(db_path=seeded_db)
    assert not df.empty
    assert (df["Team"].isin(["Cape Verde", "Curaçao", "Jordan", "Uzbekistan"])).any()


# ── filtered matches ───────────────────────────────────────────────────────────
def test_filtered_matches_no_filters(seeded_db):
    assert len(queries.filtered_matches(db_path=seeded_db)) == 104


def test_filtered_matches_by_confederation(seeded_db):
    df = queries.filtered_matches(confederation="UEFA", db_path=seeded_db)
    assert not df.empty
    assert (
        df["home"].isin(["Spain", "France", "England", "Netherlands", "Portugal"])
    ).any()


def test_filtered_matches_by_group(seeded_db):
    df = queries.filtered_matches(group_letter="A", db_path=seeded_db)
    assert not df.empty
    assert (df["group_letter"] == "A").all()


def test_filtered_matches_by_round(seeded_db):
    df = queries.filtered_matches(round_name="Final", db_path=seeded_db)
    assert not df.empty
    assert (df["round"] == "Final").all()


# ── bracket data ───────────────────────────────────────────────────────────────
def test_bracket_data_excludes_group_stage(seeded_db):
    df = queries.bracket_data(db_path=seeded_db)
    assert not df.empty
    assert (df["round"] != "Group Stage").all()


# ── connection management ──────────────────────────────────────────────────────
def test_query_returns_dataframe_and_closes_connection(seeded_db):
    df = queries.query("SELECT COUNT(*) AS n FROM teams", db_path=seeded_db)
    assert isinstance(df, pd.DataFrame)
    assert df["n"].iloc[0] == 48


def test_get_connection_usable(seeded_db):
    with queries.get_connection(db_path=seeded_db) as conn:
        assert conn.execute("SELECT 1").fetchone() == (1,)
