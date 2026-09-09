"""Genera un reporte HTML estático con Plotly comparando Mundiales."""

import os
import sqlite3

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DB_HIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "historical.db")
DB_2026 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "worldcup.db")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")


def query(sql, db_path, params=()):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def fig_to_div(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=fig.layout.title.text.replace(" ", "_"))


def build_comparison_overview():
    hist = query("SELECT * FROM world_cups ORDER BY year", DB_HIST)
    data_2026 = query(
        "SELECT COUNT(*) as total_matches, SUM(home_score + away_score) as total_goals "
        "FROM matches", DB_2026
    )

    years = list(hist["year"]) + [2026]
    champions = list(hist["champion"]) + ["Spain"]
    total_goals = list(hist["total_goals"]) + [int(data_2026["total_goals"].iloc[0])]
    total_matches = list(hist["total_matches"]) + [int(data_2026["total_matches"].iloc[0])]
    avg_goals = [round(g / m, 2) for g, m in zip(total_goals, total_matches)]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Goles totales por edición", "Promedio de goles por partido"),
        horizontal_spacing=0.12,
    )
    fig.add_trace(go.Bar(
        x=years, y=total_goals, text=total_goals, textposition="outside",
        marker_color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
        name="Goles", showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=years, y=avg_goals, mode="lines+markers+text", text=[str(v) for v in avg_goals],
        textposition="top center", line=dict(color="#d62728", width=3),
        name="Promedio", showlegend=False,
    ), row=1, col=2)
    fig.update_layout(height=400, template="plotly_white", title_text="Visión general")
    fig.update_xaxes(title_text="Año", row=1, col=1)
    fig.update_xaxes(title_text="Año", row=1, col=2)
    fig.update_yaxes(title_text="Goles", row=1, col=1)
    fig.update_yaxes(title_text="Goles/partido", row=1, col=2)
    return fig


def build_champions_timeline():
    hist = query("SELECT year, champion, runner_up, top_scorer, top_scorer_goals FROM world_cups ORDER BY year", DB_HIST)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=hist["year"].tolist() + [2026],
        y=[1] * (len(hist) + 1),
        text=hist["champion"].tolist() + ["Spain"],
        textposition="inside",
        marker_color=["#FFD700"] * len(hist) + ["#d62728"],
        textfont=dict(size=14, color="black"),
        name="Campeón",
        showlegend=False,
    ))
    fig.update_layout(
        height=250, template="plotly_white",
        title_text="Campeones recientes",
        yaxis=dict(showticklabels=False, showgrid=False),
        xaxis=dict(title="Año"),
    )
    return fig


def build_goals_by_round():
    r2026 = query(
        "SELECT round, SUM(home_score + away_score) as goals, COUNT(*) as matches "
        "FROM matches GROUP BY round ORDER BY CASE round "
        "WHEN 'Group Stage' THEN 1 WHEN 'Round of 32' THEN 2 WHEN 'Round of 16' THEN 3 "
        "WHEN 'Quarterfinal' THEN 4 WHEN 'Semifinal' THEN 5 WHEN 'Third Place' THEN 6 "
        "WHEN 'Final' THEN 7 END", DB_2026
    )
    r2026["avg"] = (r2026["goals"] / r2026["matches"]).round(2)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=r2026["round"], y=r2026["goals"],
        text=r2026["goals"], textposition="outside",
        marker_color="#1f77b4", name="Goles 2026", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=r2026["round"], y=r2026["avg"],
        text=[str(v) for v in r2026["avg"]], textposition="top center",
        mode="lines+markers", line=dict(color="#d62728", width=2),
        name="Promedio", yaxis="y2", showlegend=False,
    ))
    fig.update_layout(
        height=400, template="plotly_white",
        title_text="Goles por ronda - Mundial 2026",
        yaxis=dict(title="Goles totales"),
        yaxis2=dict(title="Promedio", overlaying="y", side="right"),
        xaxis=dict(title="Ronda"),
    )
    return fig


def build_attendance_comparison():
    att = query(
        "SELECT s.name, s.capacity, ROUND(AVG(m.attendance)) as avg_att "
        "FROM matches m JOIN stadiums s ON m.stadium_id = s.stadium_id "
        "WHERE m.attendance IS NOT NULL GROUP BY s.stadium_id ORDER BY avg_att DESC",
        DB_2026,
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=att["name"].str.split("(").str[0].str.strip(),
        y=att["avg_att"], text=att["avg_att"].astype(int),
        textposition="outside", marker_color="#2ca02c",
        name="Asistencia promedio", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=att["name"].str.split("(").str[0].str.strip(),
        y=att["capacity"], mode="lines",
        line=dict(color="#d62728", dash="dash", width=2),
        name="Capacidad", showlegend=False,
    ))
    fig.update_layout(
        height=450, template="plotly_white",
        title_text="Asistencia por estadio - Mundial 2026",
        xaxis=dict(title="Estadio", tickangle=-45),
        yaxis=dict(title="Personas"),
    )
    return fig


def build_confederation_goals():
    conf = query(
        "SELECT t.confederation, SUM(g.goals) as goals "
        "FROM goals g JOIN teams t ON g.team_id = t.team_id WHERE g.own_goal = 0 "
        "GROUP BY t.confederation ORDER BY goals DESC", DB_2026
    )

    colors = {"UEFA": "#1f77b4", "CONMEBOL": "#2ca02c", "CAF": "#ff7f0e",
              "CONCACAF": "#9467bd", "AFC": "#e377c2", "OFC": "#7f7f7f"}

    fig = go.Figure(go.Pie(
        labels=conf["confederation"], values=conf["goals"],
        marker=dict(colors=[colors.get(c, "#333") for c in conf["confederation"]]),
        textinfo="label+value+percent", hole=0.3,
    ))
    fig.update_layout(
        height=400, template="plotly_white",
        title_text="Goles por confederación - Mundial 2026",
    )
    return fig


def build_top_scorers():
    scorers = query(
        "SELECT g.scorer, t.name as team, SUM(g.goals) as goals "
        "FROM goals g JOIN teams t ON g.team_id = t.team_id WHERE g.own_goal = 0 "
        "GROUP BY g.scorer, t.name ORDER BY goals DESC LIMIT 10", DB_2026
    )

    fig = go.Figure(go.Bar(
        x=scorers["goals"], y=scorers["scorer"], orientation="h",
        text=scorers["goals"], textposition="outside",
        marker_color="#1f77b4",
    ))
    fig.update_layout(
        height=400, template="plotly_white",
        title_text="Top 10 goleadores - Mundial 2026",
        yaxis=dict(autorange="reversed"), xaxis=dict(title="Goles"),
    )
    return fig


def build_knockout_bracket():
    ko = query(
        "SELECT m.round, m.match_number, t1.name as home, m.home_score, "
        "m.away_score, t2.name as away, m.home_penalty, m.away_penalty "
        "FROM matches m JOIN teams t1 ON m.home_team_id = t1.team_id "
        "JOIN teams t2 ON m.away_team_id = t2.team_id "
        "WHERE m.round != 'Group Stage' ORDER BY m.match_number", DB_2026
    )

    fig = go.Figure()
    round_colors = {
        "Round of 32": "#aec7e8", "Round of 16": "#ffbb78",
        "Quarterfinal": "#ff9896", "Semifinal": "#c5b0d5",
        "Third Place": "#c49c94", "Final": "#f7b6d2",
    }

    for rnd in ko["round"].unique():
        subset = ko[ko["round"] == rnd]
        labels = []
        for _, row in subset.iterrows():
            score = f"{row['home_score']}-{row['away_score']}"
            if pd.notna(row["home_penalty"]):
                score += f" ({int(row['home_penalty'])}-{int(row['away_penalty'])}p)"
            labels.append(f"{row['home']} {score} {row['away']}")

        fig.add_trace(go.Bar(
            x=[rnd] * len(subset), y=list(range(len(subset))),
            text=labels, orientation="h",
            marker_color=round_colors.get(rnd, "#999"),
            name=rnd, showlegend=False,
        ))

    fig.update_layout(
        height=600, template="plotly_white",
        title_text="Llave de eliminatorias - Mundial 2026",
        yaxis=dict(showticklabels=False, showgrid=False),
    )
    return fig


def generate_html():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    figures = [
        build_comparison_overview(),
        build_champions_timeline(),
        build_goals_by_round(),
        build_attendance_comparison(),
        build_confederation_goals(),
        build_top_scorers(),
        build_knockout_bracket(),
    ]

    divs = "\n".join(fig_to_div(f) for f in figures)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mundial 2026 - Reporte Comparativo</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0f0f23;
            color: #e0e0e0;
        }}
        .hero {{
            background: linear-gradient(135deg, #1a1a3e 0%, #0d1b2a 50%, #1b2838 100%);
            padding: 80px 20px;
            text-align: center;
            border-bottom: 3px solid #d62728;
        }}
        .hero h1 {{
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(90deg, #FFD700, #FF6B35, #d62728);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .hero p {{
            font-size: 1.2rem;
            color: #8892b0;
            max-width: 600px;
            margin: 0 auto;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        .section {{
            background: #1a1a2e;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid #2a2a4a;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        .section h2 {{
            font-size: 1.5rem;
            color: #FFD700;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #2a2a4a;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #16213e, #0f3460);
            border-radius: 10px;
            padding: 25px;
            text-align: center;
            border: 1px solid #2a2a4a;
        }}
        .stat-card .number {{
            font-size: 2.5rem;
            font-weight: 800;
            color: #FFD700;
        }}
        .stat-card .label {{
            font-size: 0.9rem;
            color: #8892b0;
            margin-top: 5px;
        }}
        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: #555;
            border-top: 1px solid #2a2a4a;
        }}
        .footer a {{ color: #d62728; text-decoration: none; }}
        .footer a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>Mundial FIFA 2026</h1>
        <p>Análisis comparativo: ediciones 2014, 2018, 2022 y la nueva era de 48 selecciones</p>
    </div>

    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">104</div>
                <div class="label">Partidos jugados</div>
            </div>
            <div class="stat-card">
                <div class="number">~300</div>
                <div class="label">Goles anotados</div>
            </div>
            <div class="stat-card">
                <div class="number">48</div>
                <div class="label">Selecciones</div>
            </div>
            <div class="stat-card">
                <div class="number">3</div>
                <div class="label">Países sede</div>
            </div>
        </div>

        <div class="section">
            <h2>Visión general</h2>
            {figures[0].to_html(full_html=False, include_plotlyjs=False)}
        </div>

        <div class="section">
            <h2>Campeones recientes</h2>
            {figures[1].to_html(full_html=False, include_plotlyjs=False)}
        </div>

        <div class="section">
            <h2>Goles por ronda</h2>
            {figures[2].to_html(full_html=False, include_plotlyjs=False)}
        </div>

        <div class="section">
            <h2>Asistencia por estadio</h2>
            {figures[3].to_html(full_html=False, include_plotlyjs=False)}
        </div>

        <div class="section">
            <h2>Goles por confederación</h2>
            {figures[4].to_html(full_html=False, include_plotlyjs=False)}
        </div>

        <div class="section">
            <h2>Top goleadores</h2>
            {figures[5].to_html(full_html=False, include_plotlyjs=False)}
        </div>

        <div class="section">
            <h2>Llave de eliminatorias</h2>
            {figures[6].to_html(full_html=False, include_plotlyjs=False)}
        </div>
    </div>

    <div class="footer">
        <p>Datos generados con Python + Plotly | <a href="https://github.com/alvarosalinaso/worldcup-2026">Repositorio en GitHub</a></p>
        <p style="margin-top:8px;">Dashboard interactivo disponible en <a href="dashboard.html">Dash</a></p>
    </div>
</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Reporte generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_html()
