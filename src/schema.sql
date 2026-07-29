-- 2026 FIFA World Cup - Database Schema
-- Diseño normalizado (6 tablas) para el dashboard interactivo

CREATE TABLE IF NOT EXISTS stadiums (
    stadium_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    host_city TEXT NOT NULL,
    country TEXT NOT NULL CHECK (country IN ('USA', 'Mexico', 'Canada')),
    capacity INTEGER NOT NULL,
    region TEXT NOT NULL CHECK (region IN ('Western', 'Central', 'Eastern'))
);

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    confederation TEXT NOT NULL CHECK (confederation IN ('AFC', 'CAF', 'CONCACAF', 'CONMEBOL', 'OFC', 'UEFA')),
    fifa_ranking INTEGER,
    debut INTEGER NOT NULL DEFAULT 0 CHECK (debut IN (0, 1))
);

CREATE TABLE IF NOT EXISTS groups (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_letter TEXT NOT NULL UNIQUE CHECK (group_letter IN ('A','B','C','D','E','F','G','H','I','J','K','L'))
);

CREATE TABLE IF NOT EXISTS group_standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    pos INTEGER NOT NULL CHECK (pos BETWEEN 1 AND 4),
    played INTEGER NOT NULL DEFAULT 3,
    wins INTEGER NOT NULL DEFAULT 0,
    draws INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    goals_for INTEGER NOT NULL DEFAULT 0,
    goals_against INTEGER NOT NULL DEFAULT 0,
    goal_diff INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 0,
    qualified INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (group_id) REFERENCES groups(group_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    UNIQUE(group_id, team_id)
);

CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    round TEXT NOT NULL CHECK (round IN (
        'Group Stage', 'Round of 32', 'Round of 16',
        'Quarterfinal', 'Semifinal', 'Third Place', 'Final'
    )),
    group_letter TEXT,
    match_number INTEGER,
    date TEXT NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER NOT NULL DEFAULT 0,
    away_score INTEGER NOT NULL DEFAULT 0,
    home_penalty INTEGER,
    away_penalty INTEGER,
    extra_time INTEGER NOT NULL DEFAULT 0,
    stage_number INTEGER NOT NULL,
    stadium_id INTEGER NOT NULL,
    attendance INTEGER,
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (stadium_id) REFERENCES stadiums(stadium_id)
);

CREATE TABLE IF NOT EXISTS goals (
    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    scorer TEXT NOT NULL,
    goals INTEGER NOT NULL DEFAULT 1,
    own_goal INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS awards (
    award_id INTEGER PRIMARY KEY AUTOINCREMENT,
    award_name TEXT NOT NULL,
    recipient TEXT NOT NULL,
    team_id INTEGER,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);
