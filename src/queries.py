"""Consultas SQL analíticas sobre la base de datos del Mundial 2026."""

import os
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from typing import Any, Optional

import pandas as pd

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "worldcup.db"
)
DB_PATH = os.environ.get("WC2026_DB", DEFAULT_DB_PATH)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Devuelve una conexión SQLite (apunta a db_path o al valor por defecto)."""
    return sqlite3.connect(db_path or DB_PATH)


def query(
    sql: str,
    params: Iterable[Any] = (),
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Ejecuta una consulta SQL y devuelve un DataFrame con la conexión cerrada."""
    with closing(get_connection(db_path)) as conn:
        return pd.read_sql_query(sql, conn, params=tuple(params))


# ── GROUP STANDINGS ──
def group_table(group_letter: str, db_path: Optional[str] = None) -> pd.DataFrame:
    """Tabla de posiciones de un grupo."""
    return query(
        """
        SELECT gs.pos AS "Pos", t.name AS "Team", gs.played AS "Pld",
               gs.wins AS "W", gs.draws AS "D", gs.losses AS "L",
               gs.goals_for AS "GF", gs.goals_against AS "GA",
               gs.goal_diff AS "GD", gs.points AS "Pts"
        FROM group_standings gs
        JOIN teams t ON gs.team_id = t.team_id
        JOIN groups g ON gs.group_id = g.group_id
        WHERE g.group_letter = ?
        ORDER BY gs.pos
        """,
        [group_letter],
        db_path,
    )


# ── ALL GROUP TABLES ──
def all_group_tables(db_path: Optional[str] = None) -> pd.DataFrame:
    """Posiciones de todos los grupos."""
    return query(
        """
        SELECT g.group_letter AS "Group", gs.pos AS "#", t.name AS "Team",
               gs.played AS "W", gs.wins AS "Pld", gs.draws AS "D",
               gs.losses AS "L", gs.goals_for AS "GF", gs.goals_against AS "GA",
               gs.points AS "Pts", gs.goal_diff AS "GD", gs.qualified AS "Q"
        FROM group_standings gs
        JOIN teams t ON gs.team_id = t.team_id
        JOIN groups g ON gs.group_id = g.group_id
        ORDER BY g.group_letter, gs.pos
        """,
        db_path=db_path,
    )


# ── KNOCKOUT BRACKET ──
def knockout_matches(db_path: Optional[str] = None) -> pd.DataFrame:
    """Partidos de eliminatoria (todos salvo fase de grupos)."""
    return query(
        """
        SELECT m.round, m.date,
               t1.name AS home, m.home_score, m.home_penalty,
               t2.name AS away, m.away_score, m.away_penalty,
               m.extra_time, s.name AS stadium, m.attendance
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        JOIN stadiums s ON m.stadium_id = s.stadium_id
        WHERE m.round != 'Group Stage'
        ORDER BY m.match_number
        """,
        db_path=db_path,
    )


# ── TOP SCORERS ──
def top_scorers(limit: int = 20, db_path: Optional[str] = None) -> pd.DataFrame:
    """Ranking de goleadores (excluye autogoles)."""
    return query(
        """
        SELECT g.scorer AS "Player", t.name AS "Team", SUM(g.goals) AS "Goals"
        FROM goals g
        JOIN teams t ON g.team_id = t.team_id
        WHERE g.own_goal = 0
        GROUP BY g.scorer, t.name
        ORDER BY SUM(g.goals) DESC
        LIMIT ?
        """,
        [limit],
        db_path,
    )


# ── ATTENDANCE BY VENUE ──
def attendance_by_venue(db_path: Optional[str] = None) -> pd.DataFrame:
    """Asistencia agregada por estadio."""
    return query(
        """
        SELECT s.name AS "Stadium", s.host_city AS "City", s.country AS "Country",
               s.capacity AS "Capacity", COUNT(*) AS "Matches",
               SUM(m.attendance) AS "Total", ROUND(AVG(m.attendance)) AS "Avg"
        FROM matches m
        JOIN stadiums s ON m.stadium_id = s.stadium_id
        WHERE m.attendance IS NOT NULL
        GROUP BY s.stadium_id
        ORDER BY AVG(m.attendance) DESC
        """,
        db_path=db_path,
    )


# ── MATCHES PER DAY ──
def matches_per_day(db_path: Optional[str] = None) -> pd.DataFrame:
    """Partidos por día de torneo."""
    return query(
        """
        SELECT m.date AS "Date", COUNT(*) AS "Matches"
        FROM matches m
        GROUP BY m.date
        ORDER BY m.date
        """,
        db_path=db_path,
    )


# ── GOALS PER ROUND ──
def goals_per_round(db_path: Optional[str] = None) -> pd.DataFrame:
    """Goles y promedio por ronda."""
    return query(
        """
        SELECT m.round AS "Round",
               SUM(m.home_score + m.away_score) AS "Goals",
               COUNT(*) AS "Matches",
               ROUND(AVG(m.home_score + m.away_score), 2) AS "Avg"
        FROM matches m
        GROUP BY m.round
        ORDER BY CASE m.round
            WHEN 'Group Stage' THEN 1 WHEN 'Round of 32' THEN 2
            WHEN 'Round of 16' THEN 3 WHEN 'Quarterfinal' THEN 4
            WHEN 'Semifinal' THEN 5 WHEN 'Third Place' THEN 6
            WHEN 'Final' THEN 7
        END
        """,
        db_path=db_path,
    )


# ── TEAM PERFORMANCE ──
def team_performance(db_path: Optional[str] = None) -> pd.DataFrame:
    """Rendimiento agregado por equipo."""
    return query(
        """
        SELECT t.name AS "Team", t.confederation AS "Confed",
               COUNT(*) AS "Played",
               SUM(CASE WHEN (m.home_team_id = t.team_id AND m.home_score > m.away_score)
                            OR (m.away_team_id = t.team_id AND m.away_score > m.home_score)
                        THEN 1 ELSE 0 END) AS "Wins",
               SUM(CASE WHEN m.home_score = m.away_score THEN 1 ELSE 0 END) AS "Draws",
               SUM(CASE WHEN (m.home_team_id = t.team_id AND m.home_score < m.away_score)
                            OR (m.away_team_id = t.team_id AND m.away_score < m.home_score)
                        THEN 1 ELSE 0 END) AS "Losses",
               SUM(CASE WHEN m.home_team_id = t.team_id THEN m.home_score ELSE m.away_score END) AS "GF",
               SUM(CASE WHEN m.home_team_id = t.team_id THEN m.away_score ELSE m.home_score END) AS "GA"
        FROM teams t
        JOIN matches m ON t.team_id IN (m.home_team_id, m.away_team_id)
        GROUP BY t.team_id
        ORDER BY "Wins" DESC, "GF" - "GA" DESC
        """,
        db_path=db_path,
    )


# ── GOALS BY CONFEDERATION ──
def goals_by_confederation(db_path: Optional[str] = None) -> pd.DataFrame:
    """Goles por confederación."""
    return query(
        """
        SELECT t.confederation AS "Confederation",
               SUM(g.goals) AS "Goals",
               COUNT(DISTINCT t.team_id) AS "Teams"
        FROM goals g
        JOIN teams t ON g.team_id = t.team_id
        WHERE g.own_goal = 0
        GROUP BY t.confederation
        ORDER BY SUM(g.goals) DESC
        """,
        db_path=db_path,
    )


# ── CHAMPION PATH ──
def champion_path(db_path: Optional[str] = None) -> pd.DataFrame:
    """Partidos de España, campeón del torneo."""
    return query(
        """
        SELECT m.round AS "Round", m.date AS "Date",
               t1.name AS "Home", m.home_score ||
                   CASE WHEN m.extra_time = 1 THEN ' (a.e.t.)' ELSE '' END ||
                   CASE WHEN m.home_penalty IS NOT NULL THEN ' (' || m.home_penalty || '-' || m.away_penalty || ' pens)' ELSE '' END
               AS "Score",
               m.away_score AS "AwayScore",
               t2.name AS "Away"
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        WHERE (t1.name = 'Spain' OR t2.name = 'Spain')
          AND m.round IN ('Group Stage', 'Round of 32', 'Round of 16', 'Quarterfinal', 'Semifinal', 'Final')
        ORDER BY m.match_number
        """,
        db_path=db_path,
    )


# ── STADIUM UTILIZATION ──
def stadium_utilization(db_path: Optional[str] = None) -> pd.DataFrame:
    """Porcentaje de ocupación por estadio."""
    return query(
        """
        SELECT s.name AS "Stadium", s.host_city AS "City", s.country AS "Country",
               s.capacity AS "Capacity", COUNT(*) AS "Matches",
               ROUND(AVG(m.attendance * 100.0 / s.capacity), 1) AS "Pct_Full"
        FROM matches m
        JOIN stadiums s ON m.stadium_id = s.stadium_id
        WHERE m.attendance IS NOT NULL
        GROUP BY s.stadium_id
        ORDER BY "Pct_Full" DESC
        """,
        db_path=db_path,
    )


# ── STADIUM COORDS FOR MAP ──
def stadium_map(db_path: Optional[str] = None) -> pd.DataFrame:
    """Estadios con nº de partidos alojados (para mapa)."""
    return query(
        """
        SELECT s.name, s.host_city, s.country, s.capacity, s.region,
               COUNT(m.match_id) AS matches
        FROM stadiums s
        LEFT JOIN matches m ON s.stadium_id = m.stadium_id
        GROUP BY s.stadium_id
        """,
        db_path=db_path,
    )


# ── FULL TOURNAMENT RANKING ──
def tournament_ranking(db_path: Optional[str] = None) -> pd.DataFrame:
    """Ranking completo de los 48 equipos del torneo."""
    return query(
        """
        SELECT t.name AS "Team", t.confederation AS "Confed", t.fifa_ranking AS "FIFA Rank",
               COUNT(*) AS "Pld",
               SUM(CASE WHEN (m.home_team_id = t.team_id AND m.home_score > m.away_score)
                            OR (m.away_team_id = t.team_id AND m.away_score > m.home_score)
                        THEN 1 ELSE 0 END) AS "W",
               SUM(CASE WHEN m.home_score = m.away_score THEN 1 ELSE 0 END) AS "D",
               SUM(CASE WHEN (m.home_team_id = t.team_id AND m.home_score < m.away_score)
                            OR (m.away_team_id = t.team_id AND m.away_score < m.home_score)
                        THEN 1 ELSE 0 END) AS "L",
               SUM(CASE WHEN m.home_team_id = t.team_id THEN m.home_score ELSE m.away_score END) AS "GF",
               SUM(CASE WHEN m.home_team_id = t.team_id THEN m.away_score ELSE m.home_score END) AS "GA",
               SUM(CASE WHEN m.home_team_id = t.team_id THEN m.home_score - m.away_score ELSE m.away_score - m.home_score END) AS "GD",
               ROUND(AVG(m.home_score + m.away_score), 2) AS "Avg_Goals"
        FROM teams t
        JOIN matches m ON t.team_id IN (m.home_team_id, m.away_team_id)
        GROUP BY t.team_id
        ORDER BY "W" DESC, "GD" DESC, "GF" DESC
        """,
        db_path=db_path,
    )


# ── DEBUTANTS PERFORMANCE ──
def debutants(db_path: Optional[str] = None) -> pd.DataFrame:
    """Rendimiento de los equipos debutantes en el Mundial."""
    return query(
        """
        SELECT t.name AS "Team", t.confederation AS "Confed", t.fifa_ranking AS "Rank",
               COUNT(*) AS "Pld",
               SUM(CASE WHEN (m.home_team_id = t.team_id AND m.home_score > m.away_score)
                            OR (m.away_team_id = t.team_id AND m.away_score > m.home_score)
                        THEN 1 ELSE 0 END) AS "W",
               SUM(CASE WHEN m.home_score = m.away_score THEN 1 ELSE 0 END) AS "D",
               SUM(CASE WHEN (m.home_team_id = t.team_id AND m.home_score < m.away_score)
                            OR (m.away_team_id = t.team_id AND m.away_score < m.home_score)
                        THEN 1 ELSE 0 END) AS "L",
               SUM(CASE WHEN m.home_team_id = t.team_id THEN m.home_score ELSE m.away_score END) AS "GF",
               SUM(CASE WHEN m.home_team_id = t.team_id THEN m.away_score ELSE m.home_score END) AS "GA"
        FROM teams t
        JOIN matches m ON t.team_id IN (m.home_team_id, m.away_team_id)
        WHERE t.debut = 1
        GROUP BY t.team_id
        ORDER BY "W" DESC, "GF" - "GA" DESC
        """,
        db_path=db_path,
    )


# ── FILTERED MATCHES ──
def filtered_matches(
    confederation: Optional[str] = None,
    round_name: Optional[str] = None,
    group_letter: Optional[str] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Partidos filtrados por confederación, ronda o grupo."""
    sql = """
        SELECT m.date, m.round, m.group_letter,
               t1.name AS home, m.home_score, t2.name AS away, m.away_score,
               m.extra_time, m.home_penalty, m.away_penalty,
               s.name AS stadium, s.host_city
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        JOIN stadiums s ON m.stadium_id = s.stadium_id
        WHERE 1=1
    """
    params: list[Any] = []
    if confederation:
        sql += " AND (t1.confederation = ? OR t2.confederation = ?)"
        params.extend([confederation, confederation])
    if round_name:
        sql += " AND m.round = ?"
        params.append(round_name)
    if group_letter:
        sql += " AND m.group_letter = ?"
        params.append(group_letter)
    sql += " ORDER BY m.match_number"
    return query(sql, params, db_path)


# ── BRACKET DATA ──
def bracket_data(db_path: Optional[str] = None) -> pd.DataFrame:
    """Datos de todos los emparejamientos de eliminatoria."""
    return query(
        """
        SELECT m.match_number, m.round, m.stage_number,
               t1.name AS home, m.home_score, m.home_penalty,
               t2.name AS away, m.away_score, m.away_penalty,
               m.extra_time
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        WHERE m.round != 'Group Stage'
        ORDER BY m.match_number
        """,
        db_path=db_path,
    )
