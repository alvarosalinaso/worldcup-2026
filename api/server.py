"""Flask API que sirve datos del Mundial 2026 como JSON."""

import os
import sqlite3

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

DB_HIST = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "historical.db"
)
DB_2026 = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "worldcup.db"
)


def query(sql, db, params=()):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/overview")
def overview():
    hist = query("SELECT * FROM world_cups ORDER BY year", DB_HIST)
    stats = query(
        "SELECT COUNT(*) as matches, SUM(home_score+away_score) as goals FROM matches",
        DB_2026,
    )
    return jsonify({"history": hist, "current": stats[0]})


@app.route("/api/goals-by-round")
def goals_by_round():
    data = query(
        "SELECT round, SUM(home_score+away_score) as goals, COUNT(*) as matches, "
        "ROUND(AVG(home_score+away_score),2) as avg_goals "
        "FROM matches GROUP BY round ORDER BY CASE round "
        "WHEN 'Group Stage' THEN 1 WHEN 'Round of 32' THEN 2 WHEN 'Round of 16' THEN 3 "
        "WHEN 'Quarterfinal' THEN 4 WHEN 'Semifinal' THEN 5 WHEN 'Third Place' THEN 6 "
        "WHEN 'Final' THEN 7 END",
        DB_2026,
    )
    return jsonify(data)


@app.route("/api/goals-by-confederation")
def goals_by_confederation():
    data = query(
        "SELECT t.confederation, SUM(g.goals) as goals "
        "FROM goals g JOIN teams t ON g.team_id=t.team_id WHERE g.own_goal=0 "
        "GROUP BY t.confederation ORDER BY goals DESC",
        DB_2026,
    )
    return jsonify(data)


@app.route("/api/top-scorers")
def top_scorers():
    data = query(
        "SELECT g.scorer, t.name as team, SUM(g.goals) as goals "
        "FROM goals g JOIN teams t ON g.team_id=t.team_id WHERE g.own_goal=0 "
        "GROUP BY g.scorer, t.name ORDER BY goals DESC LIMIT 15",
        DB_2026,
    )
    return jsonify(data)


@app.route("/api/stadiums")
def stadiums():
    data = query(
        "SELECT s.name, s.host_city, s.country, s.capacity, "
        "COUNT(m.match_id) as matches, ROUND(AVG(m.attendance)) as avg_att, "
        "ROUND(AVG(m.attendance*100.0/s.capacity),1) as utilization "
        "FROM stadiums s LEFT JOIN matches m ON s.stadium_id=m.stadium_id "
        "WHERE m.attendance IS NOT NULL GROUP BY s.stadium_id ORDER BY avg_att DESC",
        DB_2026,
    )
    return jsonify(data)


@app.route("/api/teams")
def teams():
    data = query(
        "SELECT t.name, t.confederation, t.fifa_ranking, "
        "COUNT(*) as played, "
        "SUM(CASE WHEN (m.home_team_id=t.team_id AND m.home_score>m.away_score) OR "
        "(m.away_team_id=t.team_id AND m.away_score>m.home_score) THEN 1 ELSE 0 END) as wins, "
        "SUM(CASE WHEN m.home_score=m.away_score THEN 1 ELSE 0 END) as draws, "
        "SUM(CASE WHEN (m.home_team_id=t.team_id AND m.home_score<m.away_score) OR "
        "(m.away_team_id=t.team_id AND m.away_score<m.home_score) THEN 1 ELSE 0 END) as losses, "
        "SUM(CASE WHEN m.home_team_id=t.team_id THEN m.home_score ELSE m.away_score END) as gf, "
        "SUM(CASE WHEN m.home_team_id=t.team_id THEN m.away_score ELSE m.home_score END) as ga "
        "FROM teams t JOIN matches m ON t.team_id IN (m.home_team_id, m.away_team_id) "
        "GROUP BY t.team_id ORDER BY wins DESC, gf-ga DESC",
        DB_2026,
    )
    return jsonify(data)


@app.route("/api/knockout")
def knockout():
    data = query(
        "SELECT m.round, m.match_number, t1.name as home, m.home_score, "
        "m.away_score, t2.name as away, m.home_penalty, m.away_penalty, m.extra_time "
        "FROM matches m JOIN teams t1 ON m.home_team_id=t1.team_id "
        "JOIN teams t2 ON m.away_team_id=t2.team_id "
        "WHERE m.round != 'Group Stage' ORDER BY m.match_number",
        DB_2026,
    )
    return jsonify(data)


@app.route("/api/group/<letter>")
def group(letter):
    data = query(
        "SELECT gs.pos, t.name, gs.played, gs.wins, gs.draws, gs.losses, "
        "gs.goals_for, gs.goals_against, gs.goal_diff, gs.points "
        "FROM group_standings gs JOIN teams t ON gs.team_id=t.team_id "
        "JOIN groups g ON gs.group_id=g.group_id WHERE g.group_letter=? ORDER BY gs.pos",
        DB_2026,
        (letter.upper(),),
    )
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=False, port=5000)
