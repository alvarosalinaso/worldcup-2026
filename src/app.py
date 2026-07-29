import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
from queries import *

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'worldcup.db')

# Inicializa DB si no existe (para Streamlit Cloud)
if not os.path.exists(DB_PATH):
    from seed_data import init_db, seed
    init_db()
    seed()

st.set_page_config(page_title="FIFA World Cup 2026 Dashboard", layout="wide")

# ── SIDEBAR ──
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/thumb/6/6d/2026_FIFA_World_Cup_emblem.svg/240px-2026_FIFA_World_Cup_emblem.svg.png", width=120)
st.sidebar.title("FIFA World Cup 2026")
st.sidebar.markdown("*Dashboard interactivo · Proyecto de portafolio*")
st.sidebar.markdown("---")

# Filters
confeds = ['All'] + ['AFC','CAF','CONCACAF','CONMEBOL','OFC','UEFA']
f_confed = st.sidebar.selectbox("Confederation", confeds)

rounds = ['All', 'Group Stage', 'Round of 32', 'Round of 16', 'Quarterfinal', 'Semifinal', 'Third Place', 'Final']
f_round = st.sidebar.selectbox("Round", rounds)

groups = ['All'] + [chr(ord('A')+i) for i in range(12)]
f_group = st.sidebar.selectbox("Group", groups)

st.sidebar.markdown("---")
section = st.sidebar.radio("Navigation", [
    "Tournament Overview",
    "Group Stage",
    "Knockout Stage",
    "Top Scorers",
    "Venue Analysis",
    "Team Performance",
    "Champion Path",
    "Surprises & Debutants",
])

# ── HELPERS ──
@st.cache_data
def load_kwargs():
    c = query("SELECT DISTINCT round FROM matches ORDER BY CASE round WHEN 'Group Stage' THEN 1 WHEN 'Round of 32' THEN 2 WHEN 'Round of 16' THEN 3 WHEN 'Quarterfinal' THEN 4 WHEN 'Semifinal' THEN 5 WHEN 'Third Place' THEN 6 WHEN 'Final' THEN 7 END")
    g = query("SELECT group_letter FROM groups ORDER BY group_letter")
    return c['round'].tolist(), g['group_letter'].tolist()

round_list, group_list = load_kwargs()

def flag_url(team):
    f = team.lower().replace(' ','_')
    return f"https://upload.wikimedia.org/wikipedia/en/thumb/9/9a/Flag_of_Spain.svg/40px-Flag_of_Spain.svg.png"

# ── TOURNAMENT OVERVIEW ──
if section == "Tournament Overview":
    st.title("  FIFA World Cup 2026 — Interactive Dashboard")
    st.markdown("*Data Analyst Portfolio Project | Data: Wikipedia | Stack: Python, SQLite, Streamlit, Plotly*")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    df = query("SELECT COUNT(*) as n FROM teams");  t_teams = df['n'][0]
    df = query("SELECT COUNT(*) as n FROM matches"); t_matches = df['n'][0]
    df = query("SELECT SUM(home_score + away_score) as n FROM matches"); t_goals = df['n'][0]
    df = query("SELECT SUM(attendance) as n FROM matches WHERE attendance IS NOT NULL"); t_att = df['n'][0] or 6810966
    col1.metric("Teams", t_teams)
    col2.metric("Matches", t_matches)
    col3.metric("Goals", t_goals, f"{t_goals/t_matches:.2f}/match")
    col4.metric("Attendance", f"{t_att:,}", "New record")

    st.markdown("### Final Standings")
    c1, c2, c3, c4 = st.columns(4)
    c1.success(" Champion\nSpain (2nd)")
    c2.info(" Runner-up\nArgentina")
    c3.info(" Third\nEngland")
    c4.info(" Fourth\nFrance")

    st.markdown("### Awards")
    awards_df = query("SELECT award_name, recipient, t.name FROM awards a LEFT JOIN teams t ON a.team_id = t.team_id")
    for _, row in awards_df.iterrows():
        st.markdown(f"- **{row['award_name']}**: {row['recipient']} ({row['name']})")

    st.markdown("### Venues Map")
    sm = stadium_map()
    coords = {
        'Estadio Azteca': (19.3028, -99.1504),
        'MetLife Stadium': (40.8135, -74.0745),
        "AT&T Stadium": (32.7473, -97.0927),
        'SoFi Stadium': (33.9534, -118.3393),
        'Arrowhead Stadium': (39.0489, -94.4840),
        "Levi's Stadium": (37.4030, -121.9700),
        'NRG Stadium': (29.6847, -95.4107),
        'Lincoln Financial Field': (39.9008, -75.1675),
        'Mercedes-Benz Stadium': (33.7556, -84.4008),
        'Lumen Field': (47.5952, -122.3316),
        'Hard Rock Stadium': (25.9580, -80.2389),
        'Gillette Stadium': (42.0909, -71.2643),
        'BC Place': (49.2766, -123.1120),
        'Estadio BBVA': (25.6697, -100.2442),
        'Estadio Akron': (20.6817, -103.4629),
        'BMO Field': (43.6333, -79.4186),
    }
    sm['lat'] = sm['name'].str.split('(').str[0].str.strip().map(lambda x: coords.get(x, (0,0))[0])
    sm['lon'] = sm['name'].str.split('(').str[0].str.strip().map(lambda x: coords.get(x, (0,0))[1])
    fig = px.scatter_mapbox(sm, lat='lat', lon='lon', size='capacity', color='country',
                            hover_name='host_city', hover_data={'name': True, 'capacity': True, 'matches': True, 'lat': False, 'lon': False},
                            size_max=30, zoom=2.2, title='16 Host Venues Across North America',
                            color_discrete_map={'USA': '#3b82f6', 'Mexico': '#22c55e', 'Canada': '#ef4444'})
    fig.update_layout(mapbox_style='carto-positron', margin={'r':0,'t':40,'l':0,'b':0})
    st.plotly_chart(fig, use_container_width=True)

# ── GROUP STAGE ──
elif section == "Group Stage":
    st.header("Group Stage Standings")
    cols = st.columns(3)
    for idx in range(12):
        g = chr(ord('A')+idx)
        with cols[idx % 3]:
            df = group_table(g)
            qual = {1:' 1st (Q)', 2:' 2nd (Q)', 3:' 3rd', 4:' 4th'}
            df[' '] = df['Pos'].map(qual)
            st.subheader(f"Group {g}")
            st.dataframe(df[[' ','Team','Pld','W','D','L','GF','GA','GD','Pts']].style
                        .applymap(lambda v: 'background-color: #d4edda' if '(Q)' in str(v) else '', subset=[' ']),
                        hide_index=True, use_container_width=True)

    st.markdown("### Goals per Match Distribution")
    df = query("SELECT (m.home_score + m.away_score) AS goals FROM matches m WHERE m.round = 'Group Stage'")
    fig = px.histogram(df, x='goals', nbins=12, title='Group Stage Goals per Match',
                       labels={'goals': 'Goals', 'count': 'Matches'}, color_discrete_sequence=['#1f77b4'])
    fig.update_layout(bargap=0.1)
    st.plotly_chart(fig, use_container_width=True)

# ── KNOCKOUT STAGE ──
elif section == "Knockout Stage":
    st.header(" Knockout Bracket")
    bd = bracket_data()
    rounds_order = ['Round of 32', 'Round of 16', 'Quarterfinal', 'Semifinal', 'Third Place', 'Final']
    tab_labels = ['Bracket View', 'List View', 'Goals per Stage']
    tab1, tab2, tab3 = st.tabs(tab_labels)

    with tab1:
        cols = st.columns([1.8, 1.4, 1.2, 1, 0.8, 0.8])
        round_matches = {r: bd[bd['round']==r].reset_index(drop=True) for r in rounds_order}
        for ci, rnd in enumerate(rounds_order):
            with cols[min(ci, 5)]:
                st.markdown(f"**{rnd}**")
                rm = round_matches[rnd]
                for _, m in rm.iterrows():
                    et = " (a.e.t.)" if m['extra_time'] else ""
                    pen = f" ({int(m['home_penalty'])}-{int(m['away_penalty'])}p)" if pd.notna(m['home_penalty']) else ""
                    if m['home_score'] == m['away_score'] and pd.notna(m['home_penalty']):
                        winner = m['home'] if m['home_penalty'] > m['away_penalty'] else m['away']
                        txt = f"{m['home']} {int(m['home_score'])}{pen} {m['away']}"
                    else:
                        txt = f"{m['home']} {int(m['home_score'])}{et}–{int(m['away_score'])} {m['away']}"
                    st.markdown(f"<small>{txt}</small>", unsafe_allow_html=True)
                    st.markdown("---" if ci < 2 else "")

    with tab2:
        df = knockout_matches()
        for _, row in df.iterrows():
            hp = f" ({int(row['home_penalty'])}-{int(row['away_penalty'])} pens)" if pd.notna(row['home_penalty']) else ''
            et = " (a.e.t.)" if row['extra_time'] else ''
            score = f"{int(row['home_score'])}{et}{hp} – {int(row['away_score'])}"
            st.markdown(f"**{row['round']}** | {row['date']} | {row['home']} {score} {row['away']}")
            st.caption(f" {row['stadium']} | Attendance: {row['attendance']:,}" if row['attendance'] else f" {row['stadium']}")
            st.markdown("---")

    with tab3:
        gr_df = goals_per_round()
        fig = px.bar(gr_df, x='Round', y='Goals', color='Avg', text='Goals',
                     title='Goals Scored per Stage', labels={'Goals': 'Total Goals', 'Avg': 'Avg per Match'},
                     color_continuous_scale='Greens')
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

# ── TOP SCORERS ──
elif section == "Top Scorers":
    st.header(" Top Goalscorers")
    df = top_scorers(20)
    fig = px.bar(df, x='Goals', y='Player', color='Goals', text='Goals', orientation='h',
                 labels={'Player': '', 'Goals': 'Goals'}, color_continuous_scale='Blues',
                 hover_data={'Team': True})
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Golden Boot Winner")
    st.success("**Kylian Mbappé** (France) — 10 goals")
    st.markdown("Mbappé won his second consecutive Golden Boot and became the all-time World Cup leading scorer (13 total).")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Goals by Confederation")
        gbc = goals_by_confederation()
        fig = px.pie(gbc, values='Goals', names='Confederation', hole=0.4,
                     title='Goals Distribution by Confederation')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("### Goals by Tournament Stage")
        gr_df = goals_per_round()
        fig = px.bar(gr_df, x='Round', y='Goals', color='Avg', text='Goals',
                     labels={'Goals': 'Total Goals'}, color_continuous_scale='Plasma')
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

# ── VENUE ANALYSIS ──
elif section == "Venue Analysis":
    st.header(" Venue & Attendance Analysis")
    tab1, tab2, tab3 = st.tabs(["Attendance by Venue", "Utilization Rate", "Stadium Map"])

    att_df = attendance_by_venue()
    util_df = stadium_utilization()
    sm = stadium_map()
    coords = {
        'Estadio Azteca': (19.3028, -99.1504), 'MetLife Stadium': (40.8135, -74.0745),
        "AT&T Stadium": (32.7473, -97.0927), 'SoFi Stadium': (33.9534, -118.3393),
        'Arrowhead Stadium': (39.0489, -94.4840), "Levi's Stadium": (37.4030, -121.9700),
        'NRG Stadium': (29.6847, -95.4107), 'Lincoln Financial Field': (39.9008, -75.1675),
        'Mercedes-Benz Stadium': (33.7556, -84.4008), 'Lumen Field': (47.5952, -122.3316),
        'Hard Rock Stadium': (25.9580, -80.2389), 'Gillette Stadium': (42.0909, -71.2643),
        'BC Place': (49.2766, -123.1120), 'Estadio BBVA': (25.6697, -100.2442),
        'Estadio Akron': (20.6817, -103.4629), 'BMO Field': (43.6333, -79.4186),
    }
    sm['lat'] = sm['name'].str.split('(').str[0].str.strip().map(lambda x: coords.get(x, (0,0))[0])
    sm['lon'] = sm['name'].str.split('(').str[0].str.strip().map(lambda x: coords.get(x, (0,0))[1])

    with tab1:
        fig = px.bar(att_df.sort_values('Total'), x='Total', y='Stadium', color='Pct_Full',
                     text='Total', orientation='h', labels={'Total': 'Total Attendance', 'Stadium': ''},
                     color_continuous_scale='Reds',
                     hover_data={'City': True, 'Country': True, 'Capacity': True, 'Matches': True, 'Avg': True})
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = px.bar(util_df, x='Stadium', y='Pct_Full', color='Pct_Full', text='Pct_Full',
                     labels={'Pct_Full': 'Avg % Occupied'}, color_continuous_scale='RdYlGn')
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        fig.update_layout(xaxis_tickangle=-45)
        fig.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="Capacity")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = px.scatter_mapbox(sm, lat='lat', lon='lon', size='capacity', color='matches',
                                hover_name='host_city', hover_data={'name': True, 'capacity': True, 'matches': True, 'lat': False, 'lon': False},
                                size_max=30, zoom=2.5, title='Stadium Locations & Match Count',
                                color_continuous_scale='Viridis')
        fig.update_layout(mapbox_style='carto-positron', margin={'r':0,'t':40,'l':0,'b':0})
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Full Stadium Data"):
        st.dataframe(att_df[['Stadium','City','Country','Capacity','Matches','Total','Avg']],
                     hide_index=True, use_container_width=True)

# ── TEAM PERFORMANCE ──
elif section == "Team Performance":
    st.header("Team Performance Summary")
    df = team_performance()
    if f_confed != 'All':
        df = df[df['Confed'] == f_confed]
    df['GD'] = df['GF'] - df['GA']
    st.dataframe(df, hide_index=True, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Goals For vs Against")
        fig = px.scatter(df, x='GF', y='GA', size='Played', color='Played',
                         hover_name='Team', text='Team',
                         labels={'GF': 'Goals For', 'GA': 'Goals Against'},
                         color_continuous_scale='Viridis')
        fig.add_hline(y=df['GA'].median(), line_dash="dash", line_color="gray")
        fig.add_vline(x=df['GF'].median(), line_dash="dash", line_color="gray")
        fig.update_traces(textposition='top center')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top 10 by Goal Difference")
        top10 = df.sort_values('GD', ascending=False).head(10)
        fig = px.bar(top10, x='Team', y='GD', color='GD', text='GD',
                     labels={'GD': 'Goal Difference'}, color_continuous_scale='RdYlGn')
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Matches Timeline")
    mpd = matches_per_day()
    fig = px.line(mpd, x='Date', y='Matches', markers=True, title='Matches per Day')
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# ── CHAMPION PATH ──
elif section == "Champion Path":
    st.header(" Spain's Road to the Title")
    st.markdown("Spain won its **2nd World Cup title** (first since 2010), becoming the first nation to hold both men's and women's World Cups simultaneously.")
    st.markdown("Conceded only **1 goal** in the entire tournament — a record.")

    df = champion_path()
    for _, row in df.iterrows():
        if row['Home'] == 'Spain':
            text = f"**{row['Round']}**: Spain {row['Score']} {row['Away']}"
        else:
            text = f"**{row['Round']}**: {row['Home']} {row['Score']} Spain"
        st.markdown(f"- {text} ({row['Date']})")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Final: Spain 1–0 Argentina (a.e.t.)")
        st.markdown("Goal: Ferran Torres 106'")
        st.markdown("MetLife Stadium, East Rutherford | Attendance: 80,663")
    with col2:
        st.markdown("### Key Stats")
        st.markdown("- Golden Ball: Rodri")
        st.markdown("- Golden Glove: Unai Simón")
        st.markdown("- 1 goal conceded in 8 matches")
        st.markdown("- 7 wins, 1 draw — unbeaten tournament")

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Matches", "104", "+40 vs 2022")
    c2.metric("Total Goals", "308", "2.96 per match")
    c3.metric("Attendance", "6,810,966", "New record")

# ── SURPRISES & DEBUTANTS ──
else:
    st.header(" Surprises & Debutants")
    tab1, tab2, tab3 = st.tabs(["Debutants Performance", "Full Tournament Ranking", "Low Rank, High Performance"])

    with tab1:
        st.markdown("### World Cup Debutants")
        st.markdown("Four teams made their World Cup debut in 2026: Cape Verde, Curaçao, Jordan, and Uzbekistan.")
        db = debutants()
        st.dataframe(db, hide_index=True, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(db, x='Team', y='Pld', color='W', text='Pld',
                         labels={'Pld': 'Matches Played', 'W': 'Wins'}, color_continuous_scale='Blues')
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(db, x='Team', y='GF', color='W',
                         labels={'GF': 'Goals For'}, color_continuous_scale='Greens')
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        st.info(" Cape Verde was the standout debutant: undefeated in the group stage (3 draws), advanced to the Round of 32, and pushed Argentina to extra time.")

    with tab2:
        st.markdown("### Full 48-Team Tournament Ranking")
        tr = tournament_ranking()
        if f_confed != 'All':
            tr = tr[tr['Confed'] == f_confed]
        st.dataframe(tr, hide_index=True, use_container_width=True)
        fig = px.bar(tr.head(20), x='Team', y='GD', color='GD', text='GD',
                     title='Top 20 by Goal Difference', color_continuous_scale='RdYlGn')
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### Teams That Overperformed Their Ranking")
        tr = tournament_ranking()
        tr['Overperf'] = tr['FIFA Rank'] - tr['Pld'] * 2
        tr = tr.sort_values('FIFA Rank', ascending=False)
        fig = px.scatter(tr, x='FIFA Rank', y='W', size='GF', hover_name='Team', text='Team',
                         labels={'FIFA Rank': 'Pre-Tournament FIFA Ranking', 'W': 'Wins'},
                         color='Confed', title='FIFA Rank vs Tournament Wins')
        fig.update_traces(textposition='top center')
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Key Observations")
        st.markdown("- **Cape Verde** (Rank 67): Advanced to Round of 32 as debutant")
        st.markdown("- **Canada** (Rank 30): Won 1 match, advanced past group stage as host")
        st.markdown("- **DR Congo** (Rank 46): Advanced as best 3rd place from Group K")
        st.markdown("- **South Africa** (Rank 60): Advanced as 2nd in Group A over South Korea")
        st.markdown("- All top 4 seeds (Spain, Argentina, France, England) reached semifinals — first time ever")
