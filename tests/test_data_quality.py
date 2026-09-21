"""Tests for data_quality module (worldcup-2026)."""

import sqlite3
import pytest
from pathlib import Path

from src.data_quality import validate_historical_data


def test_validate_historical_data_valid(tmp_path):
    """Test validation with valid historical data."""
    db_path = tmp_path / "historical.db"
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # Create tables
    c.execute("""
        CREATE TABLE world_cups (
            wc_id INTEGER PRIMARY KEY,
            year INTEGER, host TEXT, champion TEXT, runner_up TEXT,
            top_scorer TEXT, top_scorer_goals INTEGER,
            total_matches INTEGER, total_goals INTEGER, total_attendance INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE teams (
            id INTEGER PRIMARY KEY, wc_id INTEGER, name TEXT, confederation TEXT
        )
    """)
    c.execute("""
        CREATE TABLE matches (
            id INTEGER PRIMARY KEY, wc_id INTEGER, round TEXT, group_letter TEXT,
            match_number INTEGER, date TEXT, home_team TEXT, away_team TEXT,
            home_score INTEGER, away_score INTEGER, home_penalty INTEGER,
            away_penalty INTEGER, extra_time INTEGER, attendance INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE goals (
            id INTEGER PRIMARY KEY, wc_id INTEGER, match_number INTEGER,
            team_name TEXT, scorer TEXT, goals INTEGER, own_goal INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE group_standings (
            id INTEGER PRIMARY KEY, wc_id INTEGER, group_letter TEXT,
            team_name TEXT, pos INTEGER, played INTEGER, wins INTEGER,
            draws INTEGER, losses INTEGER, goals_for INTEGER, goals_against INTEGER,
            goal_diff INTEGER, points INTEGER, qualified INTEGER
        )
    """)
    
    # Insert valid data
    c.execute("INSERT INTO world_cups VALUES (1, 2022, 'Qatar', 'Argentina', 'France', 'Mbappe', 8, 64, 172, 3400000)")
    c.execute("INSERT INTO teams VALUES (1, 1, 'Argentina', 'CONMEBOL')")
    c.execute("INSERT INTO teams VALUES (2, 1, 'France', 'UEFA')")
    c.execute("INSERT INTO matches VALUES (1, 1, 'Final', NULL, 64, '2022-12-18', 'Argentina', 'France', 3, 3, 2, 4, 1, 88966)")
    c.execute("INSERT INTO goals VALUES (1, 1, 64, 'France', 'Mbappe', 8, 0)")
    c.execute("INSERT INTO goals VALUES (2, 1, 64, 'Argentina', 'Messi', 7, 0)")
    c.execute("INSERT INTO group_standings VALUES (1, 1, 'A', 'Argentina', 1, 3, 2, 0, 1, 5, 2, 3, 6, 1)")
    c.execute("INSERT INTO group_standings VALUES (2, 1, 'A', 'France', 2, 3, 1, 1, 1, 3, 2, 1, 4, 1)")
    c.execute("INSERT INTO group_standings VALUES (3, 1, 'A', 'Poland', 3, 3, 1, 0, 2, 2, 4, -2, 3, 0)")
    c.execute("INSERT INTO group_standings VALUES (4, 1, 'A', 'Mexico', 4, 3, 0, 1, 2, 1, 3, -2, 1, 0)")
    
    conn.commit()
    conn.close()
    
    results = validate_historical_data(str(db_path))
    assert results["valid"] is True
    assert results["stats"]["world_cups_count"] == 1
    assert results["stats"]["matches_count"] == 1
    assert results["stats"]["goals_count"] == 2
    assert results["stats"]["teams_count"] == 2


def test_validate_historical_data_negative_scores(tmp_path):
    """Test validation catches negative scores."""
    db_path = tmp_path / "historical.db"
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE world_cups (
            wc_id INTEGER PRIMARY KEY, year INTEGER, host TEXT, champion TEXT,
            runner_up TEXT, top_scorer TEXT, top_scorer_goals INTEGER,
            total_matches INTEGER, total_goals INTEGER, total_attendance INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE matches (
            id INTEGER PRIMARY KEY, wc_id INTEGER, round TEXT, group_letter TEXT,
            match_number INTEGER, date TEXT, home_team TEXT, away_team TEXT,
            home_score INTEGER, away_score INTEGER, home_penalty INTEGER,
            away_penalty INTEGER, extra_time INTEGER, attendance INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE goals (
            id INTEGER PRIMARY KEY, wc_id INTEGER, match_number INTEGER,
            team_name TEXT, scorer TEXT, goals INTEGER, own_goal INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE group_standings (
            id INTEGER PRIMARY KEY, wc_id INTEGER, group_letter TEXT,
            team_name TEXT, pos INTEGER, played INTEGER, wins INTEGER,
            draws INTEGER, losses INTEGER, goals_for INTEGER, goals_against INTEGER,
            goal_diff INTEGER, points INTEGER, qualified INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE teams (
            id INTEGER PRIMARY KEY, wc_id INTEGER, name TEXT, confederation TEXT
        )
    """)
    
    c.execute("INSERT INTO world_cups VALUES (1, 2022, 'Qatar', 'Argentina', 'France', 'Mbappe', 8, 64, 172, 3400000)")
    c.execute("INSERT INTO matches VALUES (1, 1, 'Final', NULL, 64, '2022-12-18', 'Argentina', 'France', -1, 3, 2, 4, 1, 88966)")
    c.execute("INSERT INTO goals VALUES (1, 1, 64, 'France', 'Mbappe', 8, 0)")
    c.execute("INSERT INTO group_standings VALUES (1, 1, 'A', 'Argentina', 1, 3, 2, 0, 1, 5, 2, 3, 6, 1)")
    
    conn.commit()
    conn.close()
    
    results = validate_historical_data(str(db_path))
    assert results["valid"] is False
    assert any("Negative score" in e for e in results["errors"])


def test_validate_historical_data_orphan_goals(tmp_path):
    """Test validation catches goals referencing non-existent matches."""
    db_path = tmp_path / "historical.db"
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE world_cups (
            wc_id INTEGER PRIMARY KEY, year INTEGER, host TEXT, champion TEXT,
            runner_up TEXT, top_scorer TEXT, top_scorer_goals INTEGER,
            total_matches INTEGER, total_goals INTEGER, total_attendance INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE matches (
            id INTEGER PRIMARY KEY, wc_id INTEGER, round TEXT, group_letter TEXT,
            match_number INTEGER, date TEXT, home_team TEXT, away_team TEXT,
            home_score INTEGER, away_score INTEGER, home_penalty INTEGER,
            away_penalty INTEGER, extra_time INTEGER, attendance INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE goals (
            id INTEGER PRIMARY KEY, wc_id INTEGER, match_number INTEGER,
            team_name TEXT, scorer TEXT, goals INTEGER, own_goal INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE group_standings (
            id INTEGER PRIMARY KEY, wc_id INTEGER, group_letter TEXT,
            team_name TEXT, pos INTEGER, played INTEGER, wins INTEGER,
            draws INTEGER, losses INTEGER, goals_for INTEGER, goals_against INTEGER,
            goal_diff INTEGER, points INTEGER, qualified INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE teams (
            id INTEGER PRIMARY KEY, wc_id INTEGER, name TEXT, confederation TEXT
        )
    """)
    
    c.execute("INSERT INTO world_cups VALUES (1, 2022, 'Qatar', 'Argentina', 'France', 'Mbappe', 8, 64, 172, 3400000)")
    # No match 64 inserted!
    c.execute("INSERT INTO goals VALUES (1, 1, 64, 'France', 'Mbappe', 8, 0)")
    c.execute("INSERT INTO group_standings VALUES (1, 1, 'A', 'Argentina', 1, 3, 2, 0, 1, 5, 2, 3, 6, 1)")
    
    conn.commit()
    conn.close()
    
    results = validate_historical_data(str(db_path))
    assert results["valid"] is False
    assert any("non-existent match" in e for e in results["errors"])