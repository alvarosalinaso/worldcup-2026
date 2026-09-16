"""ML Match Predictor for World Cup 2026."""

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

BASE = Path(__file__).parent.parent
WC_DB = BASE / "data" / "worldcup.db"
HIST_DB = BASE / "data" / "historical.db"


def _conn(db):
    return sqlite3.connect(str(db))


def load_training_data():
    conn = _conn(HIST_DB)
    matches = pd.read_sql("SELECT * FROM matches", conn)
    teams = pd.read_sql("SELECT * FROM teams", conn)
    conn.close()

    matches = matches.rename(columns={"home_team": "home", "away_team": "away"})
    matches["label"] = matches.apply(
        lambda r: "home_win" if r["home_score"] > r["away_score"]
        else ("away_win" if r["away_score"] > r["home_score"] else "draw"),
        axis=1,
    )

    all_teams = matches["home"].unique()
    team_stats = {}
    for t in all_teams:
        team_stats[t] = {"wins": 0, "total": 0, "gf": 0, "ga": 0}

    rows = []
    for _, r in matches.iterrows():
        h, a = r["home"], r["away"]
        hs = team_stats.setdefault(h, {"wins": 0, "total": 0, "gf": 0, "ga": 0})
        aws = team_stats.setdefault(a, {"wins": 0, "total": 0, "gf": 0, "ga": 0})

        is_knockout = 1 if r["round"] != "Group Stage" else 0

        rows.append({
            "home": h,
            "away": a,
            "is_knockout": is_knockout,
            "home_win_rate": hs["wins"] / max(hs["total"], 1),
            "away_win_rate": aws["wins"] / max(aws["total"], 1),
            "home_avg_gf": hs["gf"] / max(hs["total"], 1),
            "away_avg_gf": aws["gf"] / max(aws["total"], 1),
            "home_avg_ga": hs["ga"] / max(hs["total"], 1),
            "away_avg_ga": aws["ga"] / max(aws["total"], 1),
            "label": r["label"],
        })

        hs["total"] += 1
        aws["total"] += 1
        hs["gf"] += r["home_score"]
        hs["ga"] += r["away_score"]
        aws["gf"] += r["away_score"]
        aws["ga"] += r["home_score"]
        if r["label"] == "home_win":
            hs["wins"] += 1
        elif r["label"] == "away_win":
            aws["wins"] += 1

    conn2 = _conn(WC_DB)
    wc_teams = pd.read_sql("SELECT name, fifa_ranking, confederation FROM teams", conn2)
    conn2.close()

    team_conf = {}
    team_rank = {}
    for _, t in wc_teams.iterrows():
        team_conf[t["name"]] = t["confederation"]
        team_rank[t["name"]] = t["fifa_ranking"] or 50

    for row in rows:
        row["home_conf"] = team_conf.get(row["home"], "UEFA")
        row["away_conf"] = team_conf.get(row["away"], "UEFA")
        row["rank_diff"] = team_rank.get(row["home"], 50) - team_rank.get(row["away"], 50)

    return pd.DataFrame(rows), team_conf, team_rank


def train_model():
    df, team_conf, team_rank = load_training_data()

    le_home = LabelEncoder()
    le_away = LabelEncoder()
    df["home_conf_enc"] = le_home.fit_transform(df["home_conf"])
    df["away_conf_enc"] = le_away.fit_transform(df["away_conf"])

    features = [
        "is_knockout", "home_win_rate", "away_win_rate",
        "home_avg_gf", "away_avg_gf", "home_avg_ga", "away_avg_ga",
        "home_conf_enc", "away_conf_enc", "rank_diff",
    ]
    X = df[features].fillna(0)
    y = df["label"]

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test)
    print(f"Model accuracy on test set: {accuracy:.1%}")

    return model, features, le_home, le_away, team_conf, team_rank


_model_cache = None


def _get_model():
    global _model_cache
    if _model_cache is None:
        _model_cache = train_model()
    return _model_cache


def predict_match(home_team, away_team):
    model, features, le_home, le_away, team_conf, team_rank = _get_model()

    conn = _conn(HIST_DB)
    matches = pd.read_sql("SELECT * FROM matches", conn)
    conn.close()
    matches = matches.rename(columns={"home_team": "home", "away_team": "away"})

    def _stats(name):
        wins, total, gf, ga = 0, 0, 0, 0
        for _, r in matches.iterrows():
            if r["home"] == name or r["away"] == name:
                total += 1
                is_home = r["home"] == name
                gf += r["home_score"] if is_home else r["away_score"]
                ga += r["away_score"] if is_home else r["home_score"]
                if (is_home and r["home_score"] > r["away_score"]) or \
                   (not is_home and r["away_score"] > r["home_score"]):
                    wins += 1
        return {
            "wins": wins, "total": total,
            "gf": gf / max(total, 1),
            "ga": ga / max(total, 1),
            "win_rate": wins / max(total, 1),
        }

    hs = _stats(home_team)
    aws = _stats(away_team)

    home_conf = team_conf.get(home_team, "UEFA")
    away_conf = team_conf.get(away_team, "UEFA")

    try:
        hc_enc = le_home.transform([home_conf])[0]
    except ValueError:
        hc_enc = 0
    try:
        ac_enc = le_away.transform([away_conf])[0]
    except ValueError:
        ac_enc = 0

    X_pred = pd.DataFrame([{
        "is_knockout": 0,
        "home_win_rate": hs["win_rate"],
        "away_win_rate": aws["win_rate"],
        "home_avg_gf": hs["gf"],
        "away_avg_gf": aws["gf"],
        "home_avg_ga": hs["ga"],
        "away_avg_ga": aws["ga"],
        "home_conf_enc": hc_enc,
        "away_conf_enc": ac_enc,
        "rank_diff": team_rank.get(home_team, 50) - team_rank.get(away_team, 50),
    }])

    proba = model.predict_proba(X_pred)[0]
    classes = model.classes_.tolist()

    result = {
        "home_team": home_team,
        "away_team": away_team,
        "probabilities": {c: round(float(p) * 100, 1) for c, p in zip(classes, proba)},
        "home_stats": {
            "fifa_ranking": team_rank.get(home_team, "N/A"),
            "confederation": home_conf,
            "wc_matches": hs["total"],
            "wc_win_rate": round(hs["win_rate"] * 100, 1),
        },
        "away_stats": {
            "fifa_ranking": team_rank.get(away_team, "N/A"),
            "confederation": away_conf,
            "wc_matches": aws["total"],
            "wc_win_rate": round(aws["win_rate"] * 100, 1),
        },
    }
    return result


def get_all_teams():
    conn = _conn(WC_DB)
    teams = pd.read_sql("SELECT name, fifa_ranking, confederation FROM teams ORDER BY fifa_ranking", conn)
    conn.close()
    return teams.to_dict("records")


def export_predictions(output_path=None):
    if output_path is None:
        output_path = BASE / "data" / "export" / "predictions.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    teams = [t["name"] for t in get_all_teams()[:16]]
    predictions = []
    for i, h in enumerate(teams):
        for a in teams[i + 1:]:
            try:
                pred = predict_match(h, a)
                predictions.append(pred)
            except Exception as e:
                print(f"Warning: could not predict {h} vs {a}: {e}")
                continue

    with open(output_path, "w") as f:
        json.dump(predictions, f, indent=2, ensure_ascii=False)
    return predictions


if __name__ == "__main__":
    model, features, _, _, _, _ = train_model()
    print(f"Model trained. Features: {features}")
    print(f"Classes: {model.classes_}")
    pred = predict_match("Argentina", "France")
    print(json.dumps(pred, indent=2))
