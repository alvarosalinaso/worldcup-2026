"""Crea y puebla la base de datos histórica de Mundiales (2014, 2018, 2022)."""

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "historical.db",
)
DB_PATH = os.environ.get("WC_HIST_DB", DEFAULT_DB_PATH)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS world_cups (
    wc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL UNIQUE,
    host TEXT NOT NULL,
    champion TEXT NOT NULL,
    runner_up TEXT NOT NULL,
    top_scorer TEXT NOT NULL,
    top_scorer_goals INTEGER NOT NULL,
    total_matches INTEGER NOT NULL,
    total_goals INTEGER NOT NULL,
    total_attendance INTEGER
);

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wc_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    confederation TEXT,
    FOREIGN KEY (wc_id) REFERENCES world_cups(wc_id)
);

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wc_id INTEGER NOT NULL,
    group_letter TEXT NOT NULL,
    FOREIGN KEY (wc_id) REFERENCES world_cups(wc_id)
);

CREATE TABLE IF NOT EXISTS group_standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wc_id INTEGER NOT NULL,
    group_letter TEXT NOT NULL,
    team_name TEXT NOT NULL,
    pos INTEGER NOT NULL,
    played INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    draws INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    goals_for INTEGER NOT NULL,
    goals_against INTEGER NOT NULL,
    goal_diff INTEGER NOT NULL,
    points INTEGER NOT NULL,
    qualified INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (wc_id) REFERENCES world_cups(wc_id)
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wc_id INTEGER NOT NULL,
    round TEXT NOT NULL,
    group_letter TEXT,
    match_number INTEGER,
    date TEXT,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL,
    home_penalty INTEGER,
    away_penalty INTEGER,
    extra_time INTEGER NOT NULL DEFAULT 0,
    attendance INTEGER,
    FOREIGN KEY (wc_id) REFERENCES world_cups(wc_id)
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wc_id INTEGER NOT NULL,
    match_number INTEGER,
    team_name TEXT NOT NULL,
    scorer TEXT NOT NULL,
    goals INTEGER NOT NULL DEFAULT 1,
    own_goal INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (wc_id) REFERENCES world_cups(wc_id)
);
"""


def get_conn(db_path=None):
    path = Path(db_path) if db_path else Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_historical_db(db_path=None):
    conn = get_conn(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def seed_2022(c, wc_id):
    """Qatar 2022 - Argentina champion"""
    teams = [
        ("Argentina", "CONMEBOL"), ("France", "UEFA"), ("Croatia", "UEFA"),
        ("Morocco", "CAF"), ("Netherlands", "UEFA"), ("England", "UEFA"),
        ("Brazil", "CONMEBOL"), ("Portugal", "UEFA"), ("Japan", "AFC"),
        ("Senegal", "CAF"), ("Australia", "AFC"), ("Switzerland", "UEFA"),
        ("Spain", "UEFA"), ("Poland", "UEFA"), ("South Korea", "AFC"),
        ("Germany", "UEFA"), ("United States", "CONCACAF"), ("Mexico", "CONCACAF"),
        ("Tunisia", "CAF"), ("Saudi Arabia", "AFC"), ("Ecuador", "CONMEBOL"),
        ("Cameroon", "CAF"), ("Uruguay", "CONMEBOL"), ("Ghana", "CAF"),
        ("Iran", "AFC"), ("Qatar", "AFC"), ("Wales", "UEFA"), ("Belgium", "UEFA"),
        ("Canada", "CONCACAF"), ("Costa Rica", "CONCACAF"), ("Serbia", "UEFA"),
        ("Cameroon", "CAF"),
    ]
    # Deduplicate
    seen = set()
    unique_teams = []
    for t in teams:
        if t[0] not in seen:
            seen.add(t[0])
            unique_teams.append(t)
    teams = unique_teams

    for name, conf in teams:
        c.execute("INSERT INTO teams (wc_id, name, confederation) VALUES (?,?,?)", (wc_id, name, conf))

    # Groups (A-H, 4 teams each)
    group_data = {
        "A": [("Netherlands", 1, 3, 2, 1, 0, 8, 2, 6, 7, 1),
              ("Senegal", 2, 3, 2, 0, 1, 5, 4, 1, 6, 1),
              ("Ecuador", 3, 3, 1, 1, 1, 4, 3, 1, 4, 0),
              ("Qatar", 4, 3, 0, 0, 3, 1, 7, -6, 0, 0)],
        "B": [("England", 1, 3, 2, 1, 0, 9, 2, 7, 7, 1),
              ("United States", 2, 3, 1, 2, 0, 2, 1, 1, 5, 1),
              ("Iran", 3, 3, 1, 0, 2, 4, 7, -3, 3, 0),
              ("Wales", 4, 3, 0, 1, 2, 1, 6, -5, 1, 0)],
        "C": [("Argentina", 1, 3, 2, 0, 1, 5, 2, 3, 6, 1),
              ("Poland", 2, 3, 1, 1, 1, 2, 2, 0, 4, 1),
              ("Mexico", 3, 3, 1, 1, 1, 2, 3, -1, 4, 0),
              ("Saudi Arabia", 4, 3, 1, 0, 2, 3, 5, -2, 3, 0)],
        "D": [("France", 1, 3, 2, 0, 1, 6, 3, 3, 6, 1),
              ("Australia", 2, 3, 2, 0, 1, 3, 4, -1, 6, 1),
              ("Tunisia", 3, 3, 1, 1, 1, 1, 1, 0, 4, 0),
              ("Denmark", 4, 3, 0, 1, 2, 1, 3, -2, 1, 0)],
        "E": [("Japan", 1, 3, 2, 0, 1, 4, 3, 1, 6, 1),
              ("Spain", 2, 3, 1, 1, 1, 9, 3, 6, 4, 1),
              ("Germany", 3, 3, 1, 1, 1, 6, 5, 1, 4, 0),
              ("Costa Rica", 4, 3, 1, 0, 2, 3, 11, -8, 3, 0)],
        "F": [("Morocco", 1, 3, 2, 1, 0, 4, 1, 3, 7, 1),
              ("Croatia", 2, 3, 1, 2, 0, 4, 1, 3, 5, 1),
              ("Belgium", 3, 3, 1, 1, 1, 1, 2, -1, 4, 0),
              ("Canada", 4, 3, 0, 0, 3, 2, 7, -5, 0, 0)],
        "G": [("Brazil", 1, 3, 2, 0, 1, 3, 1, 2, 6, 1),
              ("Switzerland", 2, 3, 2, 0, 1, 4, 3, 1, 6, 1),
              ("Cameroon", 3, 3, 1, 1, 1, 4, 4, 0, 4, 0),
              ("Serbia", 4, 3, 0, 1, 2, 5, 8, -3, 1, 0)],
        "H": [("Portugal", 1, 3, 2, 0, 1, 6, 4, 2, 6, 1),
              ("South Korea", 2, 3, 1, 1, 1, 4, 3, 1, 4, 1),
              ("Uruguay", 3, 3, 1, 1, 1, 2, 2, 0, 4, 0),
              ("Ghana", 4, 3, 1, 0, 2, 5, 7, -2, 3, 0)],
    }

    for g_letter, teams_list in group_data.items():
        c.execute("INSERT INTO groups (wc_id, group_letter) VALUES (?,?)", (wc_id, g_letter))
        for pos, team, pld, w, d, l, gf, ga, gd, pts, qual in teams_list:
            c.execute(
                """INSERT INTO group_standings
                (wc_id, group_letter, team_name, pos, played, wins, draws, losses,
                 goals_for, goals_against, goal_diff, points, qualified)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (wc_id, g_letter, team, pos, pld, w, d, l, gf, ga, gd, pts, qual),
            )

    # Knockout matches (real 2022 results)
    knockout = [
        ("Round of 16", None, 49, "2022-12-03", "Netherlands", "United States", 3, 1, None, None, 0, 67500),
        ("Round of 16", None, 50, "2022-12-03", "Argentina", "Australia", 2, 1, None, None, 0, 75088),
        ("Round of 16", None, 51, "2022-12-04", "France", "Poland", 3, 1, None, None, 0, 78011),
        ("Round of 16", None, 52, "2022-12-04", "England", "Senegal", 3, 0, None, None, 0, 65269),
        ("Round of 16", None, 53, "2022-12-05", "Japan", "Croatia", 1, 1, 1, 3, 1, 40845),
        ("Round of 16", None, 54, "2022-12-05", "Brazil", "South Korea", 4, 1, None, None, 0, 41842),
        ("Round of 16", None, 55, "2022-12-06", "Morocco", "Spain", 0, 0, 3, 0, 1, 63397),
        ("Round of 16", None, 56, "2022-12-06", "Portugal", "Switzerland", 6, 1, None, None, 0, 63345),
        ("Quarterfinal", None, 57, "2022-12-09", "Croatia", "Brazil", 1, 1, 4, 2, 1, 75889),
        ("Quarterfinal", None, 58, "2022-12-09", "Netherlands", "Argentina", 2, 2, 3, 4, 1, 75889),
        ("Quarterfinal", None, 59, "2022-12-10", "Morocco", "Portugal", 1, 0, None, None, 0, 62173),
        ("Quarterfinal", None, 60, "2022-12-10", "England", "France", 1, 2, None, None, 0, 65929),
        ("Semifinal", None, 61, "2022-12-13", "Argentina", "Croatia", 3, 0, None, None, 0, 68895),
        ("Semifinal", None, 62, "2022-12-14", "France", "Morocco", 2, 0, None, None, 0, 68294),
        ("Third Place", None, 63, "2022-12-17", "Croatia", "Morocco", 2, 1, None, None, 0, 44172),
        ("Final", None, 64, "2022-12-18", "Argentina", "France", 3, 3, 2, 4, 1, 88966),
    ]

    for rnd, grp, mn, dt, home, away, hs, as_, hp, ap, et, att in knockout:
        c.execute(
            """INSERT INTO matches
            (wc_id, round, group_letter, match_number, date, home_team, away_team,
             home_score, away_score, home_penalty, away_penalty, extra_time, attendance)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (wc_id, rnd, grp, mn, dt, home, away, hs, as_, hp, ap, et, att),
        )

    # Top goalscorers
    scorers = [
        (64, "France", "Kylian Mbappe", 8),
        (64, "Argentina", "Lionel Messi", 7),
        (64, "Argentina", "Julian Alvarez", 4),
        (64, "Portugal", "Goncalo Ramos", 3),
        (64, "Morocco", "Youssef En-Nesyri", 3),
        (64, "France", "Olivier Giroud", 3),
        (64, "England", "Marcus Rashford", 3),
        (64, "Ecuador", "Enner Valencia", 3),
        (64, "Japan", "Ritsu Doan", 2),
        (64, "Spain", "Alvaro Morata", 2),
    ]
    for mn, team, scorer, goals in scorers:
        c.execute(
            "INSERT INTO goals (wc_id, match_number, team_name, scorer, goals) VALUES (?,?,?,?,?)",
            (wc_id, mn, team, scorer, goals),
        )


def seed_2018(c, wc_id):
    """Russia 2018 - France champion"""
    teams = [
        ("France", "UEFA"), ("Croatia", "UEFA"), ("Belgium", "UEFA"),
        ("England", "UEFA"), ("Uruguay", "CONMEBOL"), ("Brazil", "CONMEBOL"),
        ("Sweden", "UEFA"), ("Russia", "UEFA"), ("Spain", "UEFA"),
        ("Denmark", "UEFA"), ("Mexico", "CONCACAF"), ("Switzerland", "UEFA"),
        ("Colombia", "CONMEBOL"), ("Japan", "AFC"), ("Argentina", "CONMEBOL"),
        ("Portugal", "UEFA"), ("South Korea", "AFC"), ("Nigeria", "CAF"),
        ("Germany", "UEFA"), ("Serbia", "UEFA"), ("Tunisia", "CAF"),
        ("Panama", "CONCACAF"), ("Morocco", "CAF"), ("Iran", "AFC"),
        ("Senegal", "CAF"), ("Poland", "UEFA"), ("Peru", "CONMEBOL"),
        ("Costa Rica", "CONCACAF"), ("Iceland", "UEFA"), ("Egypt", "CAF"),
        ("Australia", "AFC"), ("Saudi Arabia", "AFC"),
    ]
    seen = set()
    unique_teams = []
    for t in teams:
        if t[0] not in seen:
            seen.add(t[0])
            unique_teams.append(t)
    teams = unique_teams

    for name, conf in teams:
        c.execute("INSERT INTO teams (wc_id, name, confederation) VALUES (?,?,?)", (wc_id, name, conf))

    group_data = {
        "A": [("Uruguay", 1, 3, 3, 0, 0, 5, 0, 5, 9, 1),
              ("Russia", 2, 3, 2, 0, 1, 8, 4, 4, 6, 1),
              ("Saudi Arabia", 3, 3, 1, 0, 2, 2, 7, -5, 3, 0),
              ("Egypt", 4, 3, 0, 0, 3, 2, 6, -4, 0, 0)],
        "B": [("Spain", 1, 3, 1, 2, 0, 6, 5, 1, 5, 1),
              ("Portugal", 2, 3, 1, 2, 0, 5, 4, 1, 5, 1),
              ("Iran", 3, 3, 1, 1, 1, 2, 2, 0, 4, 0),
              ("Morocco", 4, 3, 0, 1, 2, 2, 4, -2, 1, 0)],
        "C": [("France", 1, 3, 2, 1, 0, 3, 1, 2, 7, 1),
              ("Denmark", 2, 3, 1, 2, 0, 2, 1, 1, 5, 1),
              ("Peru", 3, 3, 1, 0, 2, 2, 2, 0, 3, 0),
              ("Australia", 4, 3, 0, 1, 2, 2, 5, -3, 1, 0)],
        "D": [("Croatia", 1, 3, 3, 0, 0, 7, 1, 6, 9, 1),
              ("Argentina", 2, 3, 1, 1, 1, 3, 5, -2, 4, 1),
              ("Nigeria", 3, 3, 1, 0, 2, 3, 4, -1, 3, 0),
              ("Iceland", 4, 3, 0, 1, 2, 2, 5, -3, 1, 0)],
        "E": [("Brazil", 1, 3, 2, 1, 0, 5, 1, 4, 7, 1),
              ("Switzerland", 2, 3, 1, 2, 0, 5, 5, 0, 5, 1),
              ("Serbia", 3, 3, 1, 0, 2, 2, 4, -2, 3, 0),
              ("Costa Rica", 4, 3, 0, 1, 2, 2, 5, -3, 1, 0)],
        "F": [("Sweden", 1, 3, 2, 0, 1, 5, 2, 3, 6, 1),
              ("Mexico", 2, 3, 2, 0, 1, 3, 4, -1, 6, 1),
              ("South Korea", 3, 3, 1, 0, 2, 3, 3, 0, 3, 0),
              ("Germany", 4, 3, 1, 0, 2, 2, 4, -2, 3, 0)],
        "G": [("Belgium", 1, 3, 3, 0, 0, 9, 3, 6, 9, 1),
              ("Tunisia", 2, 3, 1, 1, 1, 5, 5, 0, 4, 1),
              ("England", 3, 3, 1, 0, 2, 5, 5, 0, 3, 1),
              ("Panama", 4, 3, 0, 0, 3, 2, 11, -9, 0, 0)],
        "H": [("Colombia", 1, 3, 2, 1, 0, 5, 2, 3, 6, 1),
              ("Japan", 2, 3, 1, 1, 1, 4, 4, 0, 4, 1),
              ("Senegal", 3, 3, 1, 1, 1, 4, 4, 0, 4, 0),
              ("Poland", 4, 3, 1, 0, 2, 2, 5, -3, 3, 0)],
    }

    for g_letter, teams_list in group_data.items():
        c.execute("INSERT INTO groups (wc_id, group_letter) VALUES (?,?)", (wc_id, g_letter))
        for pos, team, pld, w, d, l, gf, ga, gd, pts, qual in teams_list:
            c.execute(
                """INSERT INTO group_standings
                (wc_id, group_letter, team_name, pos, played, wins, draws, losses,
                 goals_for, goals_against, goal_diff, points, qualified)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (wc_id, g_letter, team, pos, pld, w, d, l, gf, ga, gd, pts, qual),
            )

    knockout = [
        ("Round of 16", None, 49, "2018-06-30", "France", "Argentina", 4, 3, None, None, 0, 78011),
        ("Round of 16", None, 50, "2018-06-30", "Uruguay", "Portugal", 2, 1, None, None, 0, 67310),
        ("Round of 16", None, 51, "2018-07-01", "Spain", "Russia", 1, 1, 3, 4, 1, 78011),
        ("Round of 16", None, 52, "2018-07-01", "Croatia", "Denmark", 1, 1, 3, 2, 1, 78011),
        ("Round of 16", None, 53, "2018-07-02", "Brazil", "Mexico", 2, 0, None, None, 0, 78011),
        ("Round of 16", None, 54, "2018-07-02", "Belgium", "Japan", 3, 2, None, None, 0, 78011),
        ("Round of 16", None, 55, "2018-07-03", "Sweden", "Switzerland", 1, 0, None, None, 0, 68723),
        ("Round of 16", None, 56, "2018-07-03", "Colombia", "England", 1, 1, 3, 4, 1, 68723),
        ("Quarterfinal", None, 57, "2018-07-06", "Uruguay", "France", 0, 2, None, None, 0, 78011),
        ("Quarterfinal", None, 58, "2018-07-06", "Brazil", "Belgium", 1, 2, None, None, 0, 78011),
        ("Quarterfinal", None, 59, "2018-07-07", "England", "Sweden", 2, 0, None, None, 0, 78011),
        ("Quarterfinal", None, 60, "2018-07-07", "Russia", "Croatia", 1, 1, 3, 4, 1, 78011),
        ("Semifinal", None, 61, "2018-07-10", "France", "Belgium", 1, 0, None, None, 0, 78011),
        ("Semifinal", None, 62, "2018-07-11", "Croatia", "England", 2, 1, None, None, 1, 78011),
        ("Third Place", None, 63, "2018-07-14", "Belgium", "England", 2, 0, None, None, 0, 63249),
        ("Final", None, 64, "2018-07-15", "France", "Croatia", 4, 2, None, None, 0, 78011),
    ]

    for rnd, grp, mn, dt, home, away, hs, as_, hp, ap, et, att in knockout:
        c.execute(
            """INSERT INTO matches
            (wc_id, round, group_letter, match_number, date, home_team, away_team,
             home_score, away_score, home_penalty, away_penalty, extra_time, attendance)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (wc_id, rnd, grp, mn, dt, home, away, hs, as_, hp, ap, et, att),
        )

    scorers = [
        (64, "England", "Harry Kane", 6),
        (64, "Belgium", "Romelu Lukaku", 4),
        (64, "France", "Antoine Griezmann", 4),
        (64, "France", "Kylian Mbappe", 4),
        (64, "Portugal", "Cristiano Ronaldo", 4),
        (64, "Spain", "Diego Costa", 3),
        (64, "Croatia", "Ivan Perisic", 3),
        (64, "Belgium", "Eden Hazard", 3),
    ]
    for mn, team, scorer, goals in scorers:
        c.execute(
            "INSERT INTO goals (wc_id, match_number, team_name, scorer, goals) VALUES (?,?,?,?,?)",
            (wc_id, mn, team, scorer, goals),
        )


def seed_2014(c, wc_id):
    """Brazil 2014 - Germany champion"""
    teams = [
        ("Germany", "UEFA"), ("Argentina", "CONMEBOL"), ("Netherlands", "UEFA"),
        ("Brazil", "CONMEBOL"), ("Colombia", "CONMEBOL"), ("Belgium", "UEFA"),
        ("France", "UEFA"), ("Costa Rica", "CONCACAF"), ("Chile", "CONMEBOL"),
        ("Nigeria", "CAF"), ("Algeria", "CAF"), ("Greece", "UEFA"),
        ("United States", "CONCACAF"), ("Switzerland", "UEFA"), ("Uruguay", "CONMEBOL"),
        ("South Korea", "AFC"), ("Mexico", "CONCACAF"), ("Croatia", "UEFA"),
        ("Japan", "AFC"), ("Portugal", "UEFA"), ("Italy", "UEFA"),
        ("Ecuador", "CONMEBOL"), ("Honduras", "CONCACAF"), ("Bosnia and Herzegovina", "UEFA"),
        ("Iran", "AFC"), ("Russia", "UEFA"), ("Ghana", "CAF"),
        ("Cameroon", "CAF"), ("Spain", "UEFA"), ("Australia", "AFC"),
        ("Ivory Coast", "CAF"), ("England", "UEFA"),
    ]
    seen = set()
    unique_teams = []
    for t in teams:
        if t[0] not in seen:
            seen.add(t[0])
            unique_teams.append(t)
    teams = unique_teams

    for name, conf in teams:
        c.execute("INSERT INTO teams (wc_id, name, confederation) VALUES (?,?,?)", (wc_id, name, conf))

    group_data = {
        "A": [("Brazil", 1, 3, 2, 1, 0, 7, 2, 5, 7, 1),
              ("Mexico", 2, 3, 2, 1, 0, 4, 1, 3, 7, 1),
              ("Croatia", 3, 3, 1, 0, 2, 6, 6, 0, 3, 0),
              ("Cameroon", 4, 3, 0, 0, 3, 1, 9, -8, 0, 0)],
        "B": [("Netherlands", 1, 3, 3, 0, 0, 10, 3, 7, 9, 1),
              ("Chile", 2, 3, 2, 0, 1, 5, 3, 2, 6, 1),
              ("Spain", 3, 3, 1, 0, 2, 4, 7, -3, 3, 0),
              ("Australia", 4, 3, 0, 0, 3, 3, 9, -6, 0, 0)],
        "C": [("Colombia", 1, 3, 3, 0, 0, 9, 2, 7, 9, 1),
              ("Greece", 2, 3, 1, 1, 1, 3, 3, 0, 4, 1),
              ("Ivory Coast", 3, 3, 1, 1, 1, 4, 5, -1, 4, 0),
              ("Japan", 4, 3, 0, 1, 2, 2, 6, -4, 1, 0)],
        "D": [("Costa Rica", 1, 3, 2, 1, 0, 4, 1, 3, 7, 1),
              ("Uruguay", 2, 3, 2, 0, 1, 4, 4, 0, 6, 1),
              ("Italy", 3, 3, 1, 0, 2, 2, 5, -3, 3, 0),
              ("England", 4, 3, 0, 1, 2, 2, 4, -2, 1, 0)],
        "E": [("France", 1, 3, 3, 0, 0, 8, 2, 6, 9, 1),
              ("Switzerland", 2, 3, 2, 0, 1, 7, 6, 1, 6, 1),
              ("Ecuador", 3, 3, 1, 1, 1, 4, 4, 0, 4, 0),
              ("Honduras", 4, 3, 0, 0, 3, 1, 8, -7, 0, 0)],
        "F": [("Argentina", 1, 3, 3, 0, 0, 6, 3, 3, 9, 1),
              ("Nigeria", 2, 3, 1, 1, 1, 3, 3, 0, 4, 1),
              ("Bosnia and Herzegovina", 3, 3, 1, 0, 2, 4, 4, 0, 3, 0),
              ("Iran", 4, 3, 0, 1, 2, 1, 4, -3, 1, 0)],
        "G": [("Germany", 1, 3, 2, 1, 0, 7, 2, 5, 7, 1),
              ("United States", 2, 3, 1, 1, 1, 4, 4, 0, 4, 1),
              ("Portugal", 3, 3, 1, 1, 1, 4, 7, -3, 4, 0),
              ("Ghana", 4, 3, 0, 1, 2, 4, 6, -2, 1, 0)],
        "H": [("Belgium", 1, 3, 3, 0, 0, 4, 1, 3, 9, 1),
              ("Algeria", 2, 3, 1, 1, 1, 6, 5, 1, 4, 1),
              ("Russia", 3, 3, 0, 2, 1, 2, 3, -1, 2, 0),
              ("South Korea", 4, 3, 0, 1, 2, 3, 6, -3, 1, 0)],
    }

    for g_letter, teams_list in group_data.items():
        c.execute("INSERT INTO groups (wc_id, group_letter) VALUES (?,?)", (wc_id, g_letter))
        for pos, team, pld, w, d, l, gf, ga, gd, pts, qual in teams_list:
            c.execute(
                """INSERT INTO group_standings
                (wc_id, group_letter, team_name, pos, played, wins, draws, losses,
                 goals_for, goals_against, goal_diff, points, qualified)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (wc_id, g_letter, team, pos, pld, w, d, l, gf, ga, gd, pts, qual),
            )

    knockout = [
        ("Round of 16", None, 49, "2014-06-28", "Brazil", "Chile", 1, 1, 3, 2, 1, 63255),
        ("Round of 16", None, 50, "2014-06-28", "Colombia", "Uruguay", 2, 0, None, None, 0, 74803),
        ("Round of 16", None, 51, "2014-06-30", "Netherlands", "Mexico", 2, 1, None, None, 0, 63987),
        ("Round of 16", None, 52, "2014-06-30", "Costa Rica", "Greece", 1, 1, 5, 3, 1, 63255),
        ("Round of 16", None, 53, "2014-07-01", "France", "Nigeria", 2, 0, None, None, 0, 67822),
        ("Round of 16", None, 54, "2014-07-01", "Germany", "Algeria", 2, 1, None, None, 1, 57970),
        ("Round of 16", None, 55, "2014-07-02", "Argentina", "Switzerland", 1, 0, None, None, 1, 63255),
        ("Round of 16", None, 56, "2014-07-02", "Belgium", "United States", 2, 1, None, None, 1, 63255),
        ("Quarterfinal", None, 57, "2014-07-04", "France", "Germany", 0, 1, None, None, 0, 63987),
        ("Quarterfinal", None, 58, "2014-07-04", "Brazil", "Colombia", 2, 1, None, None, 0, 60838),
        ("Quarterfinal", None, 59, "2014-07-05", "Argentina", "Belgium", 1, 0, None, None, 0, 63255),
        ("Quarterfinal", None, 60, "2014-07-05", "Netherlands", "Costa Rica", 0, 0, 4, 3, 1, 63255),
        ("Semifinal", None, 61, "2014-07-08", "Brazil", "Germany", 1, 7, None, None, 0, 58141),
        ("Semifinal", None, 62, "2014-07-09", "Netherlands", "Argentina", 0, 0, 2, 4, 1, 63267),
        ("Third Place", None, 63, "2014-07-12", "Brazil", "Netherlands", 0, 3, None, None, 0, 60308),
        ("Final", None, 64, "2014-07-13", "Germany", "Argentina", 1, 0, None, None, 1, 74738),
    ]

    for rnd, grp, mn, dt, home, away, hs, as_, hp, ap, et, att in knockout:
        c.execute(
            """INSERT INTO matches
            (wc_id, round, group_letter, match_number, date, home_team, away_team,
             home_score, away_score, home_penalty, away_penalty, extra_time, attendance)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (wc_id, rnd, grp, mn, dt, home, away, hs, as_, hp, ap, et, att),
        )

    scorers = [
        (64, "Colombia", "James Rodriguez", 6),
        (64, "Germany", "Thomas Muller", 5),
        (64, "Netherlands", "Robin van Persie", 4),
        (64, "Netherlands", "Arjen Robben", 3),
        (64, "Brazil", "Neymar", 4),
        (64, "France", "Karim Benzema", 3),
        (64, "Argentina", "Lionel Messi", 4),
        (64, "Germany", "Miroslav Klose", 2),
    ]
    for mn, team, scorer, goals in scorers:
        c.execute(
            "INSERT INTO goals (wc_id, match_number, team_name, scorer, goals) VALUES (?,?,?,?,?)",
            (wc_id, mn, team, scorer, goals),
        )


def seed_all_historical(db_path=None):
    conn = get_conn(db_path)
    c = conn.cursor()

    try:
        c.execute("SELECT COUNT(*) FROM world_cups")
        if c.fetchone()[0] > 0:
            print("Historical DB already seeded.")
            return

        world_cups = [
            (1, 2014, "Brazil", "Germany", "Argentina", "James Rodriguez", 6, 64, 171, 3386819),
            (2, 2018, "Russia", "France", "Croatia", "Harry Kane", 6, 64, 169, 3031768),
            (3, 2022, "Qatar", "Argentina", "France", "Kylian Mbappe", 8, 64, 172, 3404252),
        ]
        for wc_id, year, host, champ, runner, scorer, sm, tm, tg, ta in world_cups:
            c.execute(
                """INSERT INTO world_cups
                (wc_id, year, host, champion, runner_up, top_scorer, top_scorer_goals,
                 total_matches, total_goals, total_attendance)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (wc_id, year, host, champ, runner, scorer, sm, tm, tg, ta),
            )

        seed_2014(c, 1)
        seed_2018(c, 2)
        seed_2022(c, 3)

        conn.commit()
        print("Historical DB seeded successfully (2014, 2018, 2022).")
    finally:
        conn.close()


if __name__ == "__main__":
    init_historical_db()
    seed_all_historical()
