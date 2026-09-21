"""Dashboard Dash interactivo para comparar Mundiales FIFA."""

import json
import os
import sqlite3
import sys

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dash_table, dcc, html, no_update

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from src.match_predictor import predict_match, get_all_teams

DB_HIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "historical.db")
DB_2026 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "worldcup.db")

app = dash.Dash(
    __name__,
    title="Mundial 2026 Dashboard",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server


def q(sql, db, params=()):
    conn = sqlite3.connect(db)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


# Data
hist = q("SELECT * FROM world_cups ORDER BY year", DB_HIST)
teams_2026 = q("SELECT DISTINCT name, confederation FROM teams", DB_2026)
matches_2026 = q(
    "SELECT m.*, t1.name as home, t2.name as away, s.name as stadium "
    "FROM matches m JOIN teams t1 ON m.home_team_id=t1.team_id "
    "JOIN teams t2 ON m.away_team_id=t2.team_id "
    "JOIN stadiums s ON m.stadium_id=s.stadium_id", DB_2026
)

COLORS = {
    "bg": "#0a0a1a", "card": "#141428", "border": "#2a2a4a",
    "gold": "#FFD700", "text": "#e8e8e8", "muted": "#8892b0",
    "accent": "#e94560", "neon_green": "#00ffcc", "neon_blue": "#54a0ff",
}

NEON_POSTER_SVG = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='1200' height='140' viewBox='0 0 1200 140'%3E"
    "%3Crect width='1200' height='140' fill='%230a0a1a'/%3E"
    "%3Cg fill='none' stroke='%23e94560' stroke-width='2' opacity='0.8'%3E"
    "%3Cpath d='M0,110 Q200,40 400,90 T800,70 T1200,100'/%3E%3C/g%3E"
    "%3Cg fill='none' stroke='%2300ffcc' stroke-width='2' opacity='0.6'%3E"
    "%3Cpath d='M0,90 Q250,120 500,60 T900,95 T1200,70'/%3E%3C/g%3E"
    "%3Cg fill='%23FFD700' opacity='0.9'%3E"
    "%3Ccircle cx='120' cy='60' r='5'/%3E%3Ccircle cx='340' cy='95' r='4'/%3E%3Ccircle cx='620' cy='45' r='6'/%3E"
    "%3Ccircle cx='860' cy='80' r='4'/%3E%3Ccircle cx='1050' cy='55' r='5'/%3E"
    "%3C/g%3E%3Cg stroke='%2354a0ff' stroke-width='1' opacity='0.25'%3E"
    "%3Cline x1='0' y1='35' x2='1200' y2='35'/%3E%3Cline x1='0' y1='70' x2='1200' y2='70'/%3E%3Cline x1='0' y1='105' x2='1200' y2='105'/%3E"
    "%3C/g%3E%3C/svg%3E"
)


def sparkline(values, color="#e94560"):
    if not values or len(values) < 2:
        return html.Div(style={"height": "36px"})
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=list(values), mode="lines",
        line={"color": color, "width": 2.5, "shape": "spline"},
        fill="tozeroy", hoverinfo="skip", showlegend=False,
    ))
    fig.update_layout(
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False}, yaxis={"visible": False}, height=36,
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "36px"})


def insight_card(question, answer, accent="#e94560"):
    return html.Div(
        style={"backgroundColor": "#141428", "border": "1px solid #2a2a4a", "borderLeft": f"4px solid {accent}", "borderRadius": "10px", "padding": "14px 16px", "marginBottom": "12px", "boxShadow": "0 0 24px rgba(233,69,96,0.12)"},
        children=[
            html.Div(question, style={"fontWeight": "800", "textTransform": "uppercase", "fontSize": "0.72rem", "letterSpacing": "0.08em", "color": "#8892b0"}),
            html.Div(answer, style={"marginTop": "4px", "color": "#e8e8e8", "lineHeight": "1.5"}),
        ],
    )

app.layout = html.Div(style={"backgroundColor": COLORS["bg"], "minHeight": "100vh", "fontFamily": "Segoe UI, sans-serif"}, children=[
    # Header — neon abstract data-art poster
    html.Div(style={"background": "linear-gradient(135deg, #1a1a3e, #0d1b2a)", "padding": "40px 20px 0 20px", "textAlign": "center", "borderBottom": f"3px solid {COLORS['accent']}"}, children=[
        html.H1("Mundial FIFA 2026", style={"fontSize": "2.5rem", "fontWeight": "800", "color": COLORS["gold"], "margin": "0", "textShadow": "0 0 24px rgba(255,215,0,0.35)"}),
        html.P("Dashboard interactivo - Comparación de ediciones", style={"color": COLORS["muted"], "marginTop": "8px"}),
        html.Div(style={"backgroundImage": f"url(\"{NEON_POSTER_SVG}\")", "backgroundSize": "cover", "backgroundPosition": "center", "height": "140px", "marginTop": "16px", "borderTop": "1px solid #2a2a4a"}),
    ]),

    # Tabs
    dcc.Tabs(id="tabs", value="overview", style={"backgroundColor": COLORS["card"], "borderBottom": f"1px solid {COLORS['border']}"},
             children=[
                 dcc.Tab(label="Resumen", value="overview", style={"backgroundColor": COLORS["card"], "color": COLORS["text"], "border": "none"},
                         selected_style={"backgroundColor": COLORS["accent"], "color": "white", "border": "none"}),
                 dcc.Tab(label="Goles", value="goals", style={"backgroundColor": COLORS["card"], "color": COLORS["text"], "border": "none"},
                         selected_style={"backgroundColor": COLORS["accent"], "color": "white", "border": "none"}),
                 dcc.Tab(label="Estadios", value="stadiums", style={"backgroundColor": COLORS["card"], "color": COLORS["text"], "border": "none"},
                         selected_style={"backgroundColor": COLORS["accent"], "color": "white", "border": "none"}),
                 dcc.Tab(label="Equipos", value="teams", style={"backgroundColor": COLORS["card"], "color": COLORS["text"], "border": "none"},
                         selected_style={"backgroundColor": COLORS["accent"], "color": "white", "border": "none"}),
                 dcc.Tab(label="Eliminatorias", value="knockout", style={"backgroundColor": COLORS["card"], "color": COLORS["text"], "border": "none"},
                         selected_style={"backgroundColor": COLORS["accent"], "color": "white", "border": "none"}),
                 dcc.Tab(label="Predicciones ML", value="predictions", style={"backgroundColor": COLORS["card"], "color": COLORS["text"], "border": "none"},
                         selected_style={"backgroundColor": COLORS["accent"], "color": "white", "border": "none"}),
                 dcc.Tab(label="Comparar Equipos", value="compare", style={"backgroundColor": COLORS["card"], "color": COLORS["text"], "border": "none"},
                         selected_style={"backgroundColor": COLORS["accent"], "color": "white", "border": "none"}),
             ]),

    html.Div(id="tab-content", style={"maxWidth": "1100px", "margin": "0 auto", "padding": "30px 20px"}),
])


def card(title, children):
    child_list = children if isinstance(children, list) else [children]
    return html.Div(style={
        "backgroundColor": COLORS["card"], "borderRadius": "12px", "padding": "25px",
        "marginBottom": "25px", "border": f"1px solid {COLORS['border']}",
        "boxShadow": "0 4px 20px rgba(0,0,0,0.3)",
    }, children=[
        html.H3(title, style={"color": COLORS["gold"], "fontSize": "1.3rem", "marginBottom": "15px",
                              "paddingBottom": "10px", "borderBottom": f"2px solid {COLORS['border']}"}),
    ] + child_list)


def stat_row(stats):
    return html.Div(style={"display": "flex", "gap": "15px", "flexWrap": "wrap", "marginBottom": "25px"}, children=[
        html.Div(style={
            "flex": "1", "minWidth": "140px", "background": "linear-gradient(135deg, #16213e, #0f3460)",
            "borderRadius": "10px", "padding": "20px", "textAlign": "center",
            "border": f"1px solid {COLORS['border']}",
        }, children=[
            html.Div(str(val), style={"fontSize": "2rem", "fontWeight": "800", "color": COLORS["gold"]}),
            html.Div(label, style={"fontSize": "0.85rem", "color": COLORS["muted"], "marginTop": "4px"}),
        ]) for val, label in stats
    ])


@callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(tab):
    if tab == "overview":
        return overview_tab()
    elif tab == "goals":
        return goals_tab()
    elif tab == "stadiums":
        return stadiums_tab()
    elif tab == "teams":
        return teams_tab()
    elif tab == "knockout":
        return knockout_tab()
    elif tab == "predictions":
        return predictions_tab()
    elif tab == "compare":
        return compare_tab()
    return html.Div()


def overview_tab():
    att = q("SELECT COUNT(*) as m, SUM(home_score+away_score) as g FROM matches", DB_2026)
    top = q("SELECT g.scorer, t.name as team, SUM(g.goals) as goals FROM goals g JOIN teams t ON g.team_id=t.team_id WHERE g.own_goal=0 GROUP BY g.scorer, t.name ORDER BY goals DESC LIMIT 5", DB_2026)

    years = hist["year"].tolist() + [2026]
    goals = hist["total_goals"].tolist() + [int(att["g"].iloc[0])]
    avg = [round(g / m, 2) for g, m in zip(goals, [64] * 3 + [int(att["m"].iloc[0])])]

    fig_goals = go.Figure()
    fig_goals.add_trace(go.Bar(x=years, y=goals, text=goals, textposition="outside",
                               marker_color=[COLORS["muted"]] * 3 + [COLORS["accent"]]))
    fig_goals.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font_color=COLORS["text"], height=350, margin=dict(t=30, b=30))

    fig_avg = go.Figure()
    fig_avg.add_trace(go.Scatter(x=years, y=avg, mode="lines+markers+text", text=[str(v) for v in avg],
                                 textposition="top center", line=dict(color=COLORS["gold"], width=3),
                                 hovertemplate="<b>%{x}</b><br>%{y} goles/partido<extra></extra>"))
    fig_avg.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color=COLORS["text"], height=350, margin=dict(t=30, b=30),
                          yaxis_title="Goles/partido")

    return html.Div([
        stat_row([
            (int(att["m"].iloc[0]), "Partidos"),
            (int(att["g"].iloc[0]), "Goles totales"),
            ("48", "Selecciones"),
            ("3", "Sedes"),
        ]),
        card("Key Insights — Resumen ejecutivo", html.Div([
            insight_card("¿Problema?", "Comparar ediciones con distinto formato sin caer en narrativa.", COLORS["accent"]),
            insight_card("¿Metodología?", "SQLite + queries auditadas + ML con validación cruzada y disclaimers de simulación.", COLORS["neon_green"]),
            insight_card("¿Decisión?", "Qué edición fue más goleadora y qué sedes rinden más para cobertura.", COLORS["gold"]),
            sparkline(goals, COLORS["accent"]),
        ])),
        card("Evolución de goles por edición", dcc.Graph(figure=fig_goals, config={"displayModeBar": False})),
        card("Promedio de goles por partido", dcc.Graph(figure=fig_avg, config={"displayModeBar": False})),
        card("Top 5 goleadores 2026",
             dash_table.DataTable(
                 data=top.to_dict("records"),
                 columns=[{"name": c, "id": c} for c in ["scorer", "team", "goals"]],
                 style_table={"overflowX": "auto"},
                 style_header={"backgroundColor": COLORS["border"], "color": COLORS["text"], "fontWeight": "bold"},
                 style_cell={"backgroundColor": COLORS["card"], "color": COLORS["text"],
                             "border": f"1px solid {COLORS['border']}", "padding": "10px", "textAlign": "left"},
             )),
    ])


def goals_tab():
    by_round = q(
        "SELECT round, SUM(home_score+away_score) as goals, COUNT(*) as matches "
        "FROM matches GROUP BY round ORDER BY CASE round "
        "WHEN 'Group Stage' THEN 1 WHEN 'Round of 32' THEN 2 WHEN 'Round of 16' THEN 3 "
        "WHEN 'Quarterfinal' THEN 4 WHEN 'Semifinal' THEN 5 WHEN 'Third Place' THEN 6 "
        "WHEN 'Final' THEN 7 END", DB_2026
    )
    by_round["avg"] = (by_round["goals"] / by_round["matches"]).round(2)

    total = int(by_round["goals"].sum())
    fig = go.Figure()
    fig.add_trace(go.Bar(x=by_round["round"], y=by_round["goals"], text=by_round["goals"],
                         textposition="outside", name="Goles", marker_color=COLORS["accent"],
                         hovertemplate="<b>%{x}</b><br>Goles: %{y}<br>%{y:.0%} del total (" + str(total) + ")<extra>Clic para filtrar</extra>"))
    fig.add_trace(go.Scatter(x=by_round["round"], y=by_round["avg"], text=[str(v) for v in by_round["avg"]],
                             textposition="top center", mode="lines+markers", name="Promedio",
                             line=dict(color=COLORS["gold"], width=2), yaxis="y2",
                             hovertemplate="<b>%{x}</b><br>Promedio: %{y} goles/partido<extra></extra>"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color=COLORS["text"], height=400, margin=dict(t=30),
                      yaxis=dict(title="Goles totales"), yaxis2=dict(title="Promedio", overlaying="y", side="right"))

    conf = q("SELECT t.confederation, SUM(g.goals) as goals FROM goals g JOIN teams t ON g.team_id=t.team_id WHERE g.own_goal=0 GROUP BY t.confederation ORDER BY goals DESC", DB_2026)
    fig_conf = px.pie(conf, names="confederation", values="goals", hole=0.3,
                      color_discrete_sequence=px.colors.qualitative.Set2)
    fig_conf.update_traces(hovertemplate="<b>%{label}</b><br>Goles: %{value}<br>%{percent}<extra></extra>")
    fig_conf.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color=COLORS["text"], height=400)

    return html.Div([
        card("Goles por ronda — clic una barra para filtrar", html.Div([
            dcc.Graph(id="goals-round-bar", figure=fig, config={"displayModeBar": False}),
            html.Div(id="goals-crossfilter-output", style={"marginTop": "8px", "color": COLORS["gold"], "fontWeight": "700"}),
        ])),
        card("Distribución por confederación", dcc.Graph(figure=fig_conf, config={"displayModeBar": False})),
    ])


@callback(
    Output("goals-crossfilter-output", "children"),
    Input("goals-round-bar", "clickData"),
    prevent_initial_call=True,
)
def goals_crossfilter(click):
    if not click:
        return no_update
    r = click["points"][0].get("x", "?")
    return f"Ronda seleccionada: {r} — úsala para filtrar Eliminatorias y Equipos."


def stadiums_tab():
    att = q(
        "SELECT s.name, s.host_city, s.country, s.capacity, "
        "COUNT(*) as matches, ROUND(AVG(m.attendance)) as avg_att, "
        "ROUND(AVG(m.attendance*100.0/s.capacity),1) as pct "
        "FROM matches m JOIN stadiums s ON m.stadium_id=s.stadium_id "
        "WHERE m.attendance IS NOT NULL GROUP BY s.stadium_id ORDER BY avg_att DESC", DB_2026
    )

    short_name = att["name"].str.split("(").str[0].str.strip()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=short_name, y=att["avg_att"], text=att["avg_att"].astype(int),
                         textposition="outside", name="Asistencia", marker_color="#2ca02c"))
    fig.add_trace(go.Scatter(x=short_name, y=att["capacity"], mode="lines",
                             line=dict(color=COLORS["accent"], dash="dash"), name="Capacidad"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color=COLORS["text"], height=450, margin=dict(t=30),
                      xaxis=dict(tickangle=-45), yaxis=dict(title="Personas"))

    return html.Div([
        card("Asistencia vs Capacidad", dcc.Graph(figure=fig, config={"displayModeBar": False})),
        card("Detalle por estadio",
             dash_table.DataTable(
                 data=att[["name", "host_city", "country", "capacity", "matches", "avg_att", "pct"]].to_dict("records"),
                 columns=[{"name": c, "id": c} for c in ["name", "host_city", "country", "capacity", "matches", "avg_att", "pct"]],
                 sort_action="native",
                 style_table={"overflowX": "auto"},
                 style_header={"backgroundColor": COLORS["border"], "color": COLORS["text"], "fontWeight": "bold"},
                 style_cell={"backgroundColor": COLORS["card"], "color": COLORS["text"],
                             "border": f"1px solid {COLORS['border']}", "padding": "8px", "textAlign": "left"},
             )),
    ])


def teams_tab():
    perf = q(
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
        "GROUP BY t.team_id ORDER BY wins DESC, gf-ga DESC", DB_2026
    )

    fig = go.Figure()
    top16 = perf.head(16)
    fig.add_trace(go.Bar(x=top16["name"], y=top16["wins"], name="Victorias", marker_color="#2ca02c"))
    fig.add_trace(go.Bar(x=top16["name"], y=top16["draws"], name="Empates", marker_color=COLORS["muted"]))
    fig.add_trace(go.Bar(x=top16["name"], y=top16["losses"], name="Derrotas", marker_color=COLORS["accent"]))
    fig.update_layout(barmode="stack", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color=COLORS["text"], height=450, margin=dict(t=30, b=30),
                      xaxis=dict(tickangle=-45), legend=dict(orientation="h", y=1.1))

    return html.Div([
        card("Rendimiento top 16 equipos", dcc.Graph(figure=fig, config={"displayModeBar": False})),
        card("Tabla completa",
             dash_table.DataTable(
                 data=perf.to_dict("records"),
                 columns=[{"name": c, "id": c} for c in perf.columns],
                 sort_action="native", page_size=15,
                 style_table={"overflowX": "auto"},
                 style_header={"backgroundColor": COLORS["border"], "color": COLORS["text"], "fontWeight": "bold"},
                 style_cell={"backgroundColor": COLORS["card"], "color": COLORS["text"],
                             "border": f"1px solid {COLORS['border']}", "padding": "8px", "textAlign": "left"},
             )),
    ])


def knockout_tab():
    ko = q(
        "SELECT m.round, m.match_number, t1.name as home, m.home_score, "
        "m.away_score, t2.name as away, m.home_penalty, m.away_penalty, m.extra_time "
        "FROM matches m JOIN teams t1 ON m.home_team_id=t1.team_id "
        "JOIN teams t2 ON m.away_team_id=t2.team_id "
        "WHERE m.round != 'Group Stage' ORDER BY m.match_number", DB_2026
    )

    rows = []
    for _, r in ko.iterrows():
        score = f"{r['home_score']}-{r['away_score']}"
        if pd.notna(r["home_penalty"]):
            score += f" ({int(r['home_penalty'])}-{int(r['away_penalty'])} pen)"
        if r["extra_time"]:
            score += " (a.e.t.)"
        rows.append({"Ronda": r["round"], "Local": r["home"], "Marcador": score, "Visitante": r["away"]})

    return html.Div([
        card("Llave de eliminatorias",
             dash_table.DataTable(
                 data=rows,
                 columns=[{"name": c, "id": c} for c in ["Ronda", "Local", "Marcador", "Visitante"]],
                 sort_action="native",
                 style_table={"overflowX": "auto"},
                 style_header={"backgroundColor": COLORS["border"], "color": COLORS["text"], "fontWeight": "bold"},
                 style_cell={"backgroundColor": COLORS["card"], "color": COLORS["text"],
                             "border": f"1px solid {COLORS['border']}", "padding": "12px", "textAlign": "center"},
                 style_data_conditional=[
                     {"if": {"filter_query": '{Ronda} = "Final"'},
                      "backgroundColor": "#2a1a1a", "fontWeight": "bold"},
                     {"if": {"filter_query": '{Ronda} = "Semifinal"'},
                      "backgroundColor": "#1a1a2e"},
                 ],
             )),
    ])


# ── ML Predictions ─────────────────────────────────────────────────────────────

_team_list = [t["name"] for t in get_all_teams()]
# Model loads lazily on first predict_match() call via _get_model()


def predictions_tab():
    return html.Div([
        card("Predicción de Partidos — Random Forest", [
            html.Div(style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "marginBottom": "20px"}, children=[
                html.Div(style={"flex": "1", "minWidth": "200px"}, children=[
                    html.Label("Equipo Local", style={"color": COLORS["muted"], "fontSize": "0.9rem"}),
                    dcc.Dropdown(id="pred-home", options=[{"label": t, "value": t} for t in _team_list],
                                 value="Argentina", style={"backgroundColor": COLORS["bg"], "color": "#000"}),
                ]),
                html.Div(style={"flex": "1", "minWidth": "200px"}, children=[
                    html.Label("Equipo Visitante", style={"color": COLORS["muted"], "fontSize": "0.9rem"}),
                    dcc.Dropdown(id="pred-away", options=[{"label": t, "value": t} for t in _team_list],
                                 value="France", style={"backgroundColor": COLORS["bg"], "color": "#000"}),
                ]),
            ]),
            html.Button("Predecir", id="pred-btn", n_clicks=0,
                        style={"backgroundColor": COLORS["accent"], "color": "white", "border": "none",
                               "padding": "10px 30px", "borderRadius": "8px", "cursor": "pointer",
                               "fontWeight": "700", "fontSize": "1rem"}),
        ]),
        html.Div(id="pred-result"),
    ])


@callback(
    Output("pred-result", "children"),
    Input("pred-btn", "n_clicks"),
    State("pred-home", "value"),
    State("pred-away", "value"),
)
def update_prediction(n_clicks, home, away):
    if n_clicks == 0 or not home or not away:
        return html.Div()
    if home == away:
        return card("Error", html.P("Selecciona dos equipos diferentes"))

    pred = predict_match(home, away)
    probs = pred["probabilities"]

    labels = []
    values = []
    colors = []
    for k, label in [("home_win", f"{home} victoria"), ("draw", "Empate"), ("away_win", f"{away} victoria")]:
        if k in probs:
            labels.append(label)
            values.append(probs[k])
            colors.append(COLORS["gold"] if k == "home_win" else (COLORS["muted"] if k == "draw" else COLORS["accent"]))

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h", text=[f"{v}%" for v in values],
        textposition="outside", marker_color=colors,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["text"], height=200, margin=dict(t=10, b=10, l=10, r=10),
        xaxis=dict(range=[0, 100], title="%"),
    )

    hs = pred["home_stats"]
    aws = pred["away_stats"]

    def team_card(name, stats, color):
        return html.Div(style={
            "flex": "1", "minWidth": "200px", "backgroundColor": COLORS["bg"],
            "borderRadius": "10px", "padding": "15px", "border": f"2px solid {color}",
        }, children=[
            html.Div(name, style={"fontWeight": "700", "color": color, "fontSize": "1.1rem", "marginBottom": "10px"}),
            html.Div(f"Ranking FIFA: {stats['fifa_ranking']}", style={"color": COLORS["text"]}),
            html.Div(f"Confederación: {stats['confederation']}", style={"color": COLORS["text"]}),
            html.Div(f"Partidos WC: {stats['wc_matches']}", style={"color": COLORS["text"]}),
            html.Div(f"Win rate: {stats['wc_win_rate']}%", style={"color": COLORS["text"]}),
        ])

    return html.Div([
        card("Probabilidades", dcc.Graph(figure=fig, config={"displayModeBar": False})),
        card("Comparación de Estadísticas", html.Div(style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}, children=[
            team_card(home, hs, COLORS["gold"]),
            team_card(away, aws, COLORS["accent"]),
        ])),
    ])


def compare_tab():
    return html.Div([
        card("Comparar Equipos — Radar Chart", [
            html.Div(style={"marginBottom": "20px"}, children=[
                html.Label("Selecciona 2-4 equipos", style={"color": COLORS["muted"], "fontSize": "0.9rem"}),
                dcc.Dropdown(id="compare-teams", options=[{"label": t, "value": t} for t in _team_list],
                             multi=True, maxValues=4, value=["Argentina", "France", "Brazil", "Germany"],
                             style={"backgroundColor": COLORS["bg"], "color": "#000"}),
            ]),
        ]),
        html.Div(id="compare-result"),
    ])


@callback(Output("compare-result", "children"), Input("compare-teams", "value"))
def update_comparison(selected):
    if not selected or len(selected) < 2:
        return card("Selecciona al menos 2 equipos", html.P(""))

    conn = sqlite3.connect(DB_2026)
    perf = pd.read_sql_query(
        "SELECT t.name, t.fifa_ranking, t.confederation, "
        "COUNT(*) as played, "
        "SUM(CASE WHEN (m.home_team_id=t.team_id AND m.home_score>m.away_score) OR "
        "(m.away_team_id=t.team_id AND m.away_score>m.home_score) THEN 1 ELSE 0 END) as wins, "
        "SUM(CASE WHEN m.home_score=m.away_score THEN 1 ELSE 0 END) as draws, "
        "SUM(CASE WHEN (m.home_team_id=t.team_id AND m.home_score<m.away_score) OR "
        "(m.away_team_id=t.team_id AND m.away_score<m.home_score) THEN 1 ELSE 0 END) as losses, "
        "SUM(CASE WHEN m.home_team_id=t.team_id THEN m.home_score ELSE m.away_score END) as gf, "
        "SUM(CASE WHEN m.home_team_id=t.team_id THEN m.away_score ELSE m.home_score END) as ga "
        "FROM teams t JOIN matches m ON t.team_id IN (m.home_team_id, m.away_team_id) "
        "WHERE t.name IN ({}) GROUP BY t.team_id".format(",".join("?" * len(selected))),
        conn, params=selected,
    )
    conn.close()

    if perf.empty:
        return card("No hay datos", html.P(""))

    categories = ["Ranking (inv)", "Victoria GF", "Goles a favor", "Diferencia GF-GA", "Puntos"]
    fig_radar = go.Figure()
    for _, row in perf.iterrows():
        max_rank = perf["fifa_ranking"].max() or 100
        vals = [
            (1 - row["fifa_ranking"] / max_rank) * 100 if row["fifa_ranking"] else 50,
            row["wins"] / max(row["played"], 1) * 100,
            row["gf"] / max(row["played"], 1) * 20,
            max(row["gf"] - row["ga"], 0) * 5,
            row["wins"] * 3 + row["draws"],
        ]
        fig_radar.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=categories + [categories[0]],
                                             fill="toself", name=row["name"]))
    fig_radar.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, 100])),
        paper_bgcolor="rgba(0,0,0,0)", font_color=COLORS["text"], height=450,
        legend=dict(font=dict(color=COLORS["text"])),
    )

    fig_bar = go.Figure()
    metrics = ["played", "wins", "draws", "losses", "gf", "ga"]
    labels = ["Jugados", "Victorias", "Empates", "Derrotas", "GF", "GC"]
    bar_colors = ["#2ca02c", COLORS["gold"], COLORS["muted"], COLORS["accent"], "#1f77b4", "#ff7f0e"]
    for i, m in enumerate(metrics):
        fig_bar.add_trace(go.Bar(x=perf["name"], y=perf[m], name=labels[i], marker_color=bar_colors[i]))
    fig_bar.update_layout(
        barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["text"], height=400, legend=dict(orientation="h", y=1.15),
    )

    return html.Div([
        card("Radar de Comparación", dcc.Graph(figure=fig_radar, config={"displayModeBar": False})),
        card("Estadísticas Comparadas", dcc.Graph(figure=fig_bar, config={"displayModeBar": False})),
        card("Tabla Detallada",
             dash_table.DataTable(
                 data=perf.to_dict("records"),
                 columns=[{"name": c, "id": c} for c in perf.columns],
                 style_table={"overflowX": "auto"},
                 style_header={"backgroundColor": COLORS["border"], "color": COLORS["text"], "fontWeight": "bold"},
                 style_cell={"backgroundColor": COLORS["card"], "color": COLORS["text"],
                             "border": f"1px solid {COLORS['border']}", "padding": "8px", "textAlign": "left"},
             )),
    ])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8050)))
