"""Tests for match_predictor module (worldcup-2026)."""

import sqlite3
import pandas as pd
import pytest
from pathlib import Path

from src.match_predictor import load_training_data, train_model, predict_match, get_all_teams


def _setup_databases(tmp_path):
    """Create test historical and worldcup databases."""
    hist_db = tmp_path / "historical.db"
    wc_db = tmp_path / "worldcup.db"
    
    # Historical DB
    conn = sqlite3.connect(str(hist_db))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE world_cups (
            wc_id INTEGER PRIMARY KEY, year INTEGER, host TEXT, champion TEXT,
            runner_up TEXT, top_scorer TEXT, top_scorer_goals INTEGER,
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
    
    # Insert test data for 2014, 2018, 2022
    world_cups = [
        (1, 2014, "Brazil", "Germany", "Argentina", "James Rodriguez", 6, 64, 171, 3386819),
        (2, 2018, "Russia", "France", "Croatia", "Harry Kane", 6, 64, 169, 3031768),
        (3, 2022, "Qatar", "Argentina", "France", "Kylian Mbappe", 8, 64, 172, 3404252),
    ]
    for wc in world_cups:
        c.execute("INSERT INTO world_cups VALUES (?,?,?,?,?,?,?,?,?,?)", wc)
    
    # Teams for each WC
    teams_data = [
        (1, "Germany", "UEFA"), (1, "Argentina", "CONMEBOL"), (1, "Netherlands", "UEFA"),
        (1, "Brazil", "CONMEBOL"), (1, "France", "UEFA"), (1, "Belgium", "UEFA"),
        (2, "France", "UEFA"), (2, "Croatia", "UEFA"), (2, "Belgium", "UEFA"),
        (2, "England", "UEFA"), (2, "Argentina", "CONMEBOL"), (2, "Brazil", "CONMEBOL"),
        (3, "Argentina", "CONMEBOL"), (3, "France", "UEFA"), (3, "Croatia", "UEFA"),
        (3, "Morocco", "CAF"), (3, "Brazil", "CONMEBOL"), (3, "Netherlands", "UEFA"),
    ]
    for wc_id, name, conf in teams_data:
        c.execute("INSERT INTO teams (wc_id, name, confederation) VALUES (?,?,?)", (wc_id, name, conf))
    
    # Matches with variety of results
    matches_data = [
        # 2014
        (1, "Round of 16", None, 49, "2014-06-28", "Brazil", "Chile", 1, 1, 3, 2, 1, 63255),
        (1, "Quarterfinal", None, 57, "2014-07-04", "France", "Germany", 0, 1, None, None, 0, 63987),
        (1, "Semifinal", None, 61, "2014-07-08", "Brazil", "Germany", 1, 7, None, None, 0, 58141),
        (1, "Final", None, 64, "2014-07-13", "Germany", "Argentina", 1, 0, None, None, 1, 74738),
        # 2018
        (2, "Round of 16", None, 49, "2018-06-30", "France", "Argentina", 4, 3, None, None, 0, 78011),
        (2, "Quarterfinal", None, 57, "2018-07-06", "Uruguay", "France", 0, 2, None, None, 0, 78011),
        (2, "Semifinal", None, 61, "2018-07-10", "France", "Belgium", 1, 0, None, None, 0, 78011),
        (2, "Final", None, 64, "2018-07-15", "France", "Croatia", 4, 2, None, None, 0, 78011),
        # 2022
        (3, "Round of 16", None, 49, "2022-12-03", "Netherlands", "United States", 3, 1, None, None, 0, 67500),
        (3, "Quarterfinal", None, 57, "2022-12-09", "Croatia", "Brazil", 1, 1, 4, 2, 1, 75889),
        (3, "Semifinal", None, 61, "2022-12-13", "Argentina", "Croatia", 3, 0, None, None, 0, 68895),
        (3, "Final", None, 64, "2022-12-18", "Argentina", "France", 3, 3, 2, 4, 1, 88966),
    ]
    for m in matches_data:
        c.execute("""
            INSERT INTO matches (wc_id, round, group_letter, match_number, date, home_team, away_team,
                                home_score, away_score, home_penalty, away_penalty, extra_time, attendance)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, m)
    
    # Goals
    goals_data = [
        (64, "Germany", "Thomas Muller", 5), (64, "Netherlands", "Robin van Persie", 4),
        (64, "Argentina", "Lionel Messi", 4), (64, "France", "Antoine Griezmann", 4),
        (64, "France", "Kylian Mbappe", 4), (64, "Portugal", "Cristiano Ronaldo", 4),
        (64, "Spain", "Diego Costa", 3), (64, "Croatia", "Ivan Perisic", 3),
        (64, "Belgium", "Eden Hazard", 3),
        (64, "France", "Kylian Mbappe", 8), (64, "Argentina", "Lionel Messi", 7),
        (64, "Argentina", "Julian Alvarez", 4), (64, "Portugal", "Goncalo Ramos", 3),
        (64, "Morocco", "Youssef En-Nesyri", 3), (64, "France", "Olivier Giroud", 3),
        (64, "England", "Marcus Rashford", 3), (64, "Ecuador", "Enner Valencia", 3),
        (64, "Japan", "Ritsu Doan", 2), (64, "Spain", "Alvaro Morata", 2),
    ]
    for mn, team, scorer, goals in goals_data:
        c.execute("INSERT INTO goals (wc_id, match_number, team_name, scorer, goals) VALUES (?,?,?,?,?)", (3, mn, team, scorer, goals))
    
    conn.commit()
    conn.close()
    
    # Worldcup DB (2026 teams)
    conn = sqlite3.connect(str(wc_db))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE teams (
            team_id INTEGER PRIMARY KEY, name TEXT, confederation TEXT, fifa_ranking INTEGER, debut INTEGER
        )
    """)
    wc_teams = [
        ("Argentina", "CONMEBOL", 1, 0), ("France", "UEFA", 2, 0), ("Brazil", "CONMEBOL", 3, 0),
        ("England", "UEFA", 4, 0), ("Belgium", "UEFA", 5, 0), ("Croatia", "UEFA", 6, 0),
        ("Netherlands", "UEFA", 7, 0), ("Portugal", "UEFA", 8, 0), ("Spain", "UEFA", 9, 0),
        ("Morocco", "CAF", 10, 0), ("Germany", "UEFA", 11, 0), ("Uruguay", "CONMEBOL", 12, 0),
        ("USA", "CONCACAF", 13, 0), ("Mexico", "CONCACAF", 14, 0), ("Japan", "AFC", 15, 0),
        ("Senegal", "CAF", 16, 0),
    ]
    for name, conf, rank, debut in wc_teams:
        c.execute("INSERT INTO teams (name, confederation, fifa_ranking, debut) VALUES (?,?,?,?)", (name, conf, rank, debut))
    conn.commit()
    conn.close()
    
    return str(hist_db), str(wc_db)


def test_load_training_data(tmp_path, monkeypatch):
    """Test loading training data from historical DB."""
    hist_db, wc_db = _setup_databases(tmp_path)
    
    import src.match_predictor as mp
    monkeypatch.setattr(mp, "HIST_DB", Path(hist_db))
    monkeypatch.setattr(mp, "WC_DB", Path(wc_db))
    
    df, team_conf, team_rank = load_training_data()
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "label" in df.columns
    assert "home_win_rate" in df.columns
    assert "rank_diff" in df.columns
    assert isinstance(team_conf, dict)
    assert isinstance(team_rank, dict)
    assert "Argentina" in team_conf
    assert team_rank["Argentina"] == 1


def test_train_model(tmp_path, monkeypatch):
    """Test model training with cross-validation."""
    hist_db, wc_db = _setup_databases(tmp_path)
    
    import src.match_predictor as mp
    monkeypatch.setattr(mp, "HIST_DB", Path(hist_db))
    monkeypatch.setattr(mp, "WC_DB", Path(wc_db))
    
    model, features, le_home, le_away, team_conf, team_rank = train_model(cv_folds=3)
    
    assert model is not None
    assert len(features) == 10
    assert "is_knockout" in features
    assert "rank_diff" in features
    assert hasattr(model, "predict_proba")


def test_predict_match(tmp_path, monkeypatch):
    """Test match prediction."""
    hist_db, wc_db = _setup_databases(tmp_path)
    
    import src.match_predictor as mp
    monkeypatch.setattr(mp, "HIST_DB", Path(hist_db))
    monkeypatch.setattr(mp, "WC_DB", Path(wc_db))
    
    result = predict_match("Argentina", "France")
    
    assert "home_team" in result
    assert "away_team" in result
    assert "probabilities" in result
    assert "home_stats" in result
    assert "away_stats" in result
    assert result["home_team"] == "Argentina"
    assert result["away_team"] == "France"
    assert sum(result["probabilities"].values()) > 0
    
    # Probabilities should sum to ~100
    total_prob = sum(result["probabilities"].values())
    assert 99 <= total_prob <= 101


def test_get_all_teams(tmp_path, monkeypatch):
    """Test getting all 2026 teams."""
    hist_db, wc_db = _setup_databases(tmp_path)
    
    import src.match_predictor as mp
    monkeypatch.setattr(mp, "HIST_DB", Path(hist_db))
    monkeypatch.setattr(mp, "WC_DB", Path(wc_db))
    
    teams = get_all_teams()
    
    assert isinstance(teams, list)
    assert len(teams) == 16
    assert all("name" in t and "confederation" in t and "fifa_ranking" in t for t in teams)
    # Should be sorted by ranking
    rankings = [t["fifa_ranking"] for t in teams]
    assert rankings == sorted(rankings)