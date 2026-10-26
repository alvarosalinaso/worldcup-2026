"""ML Match Predictor del Mundial 2026 con evaluación honesta (sin leakage).

LIMITACIONES (revisado en la revisión 2026-10):
- Entrenado con 48 partidos (octavos -> final) de los Mundiales 2014, 2018 y
  2022 (data/historical.db NO incluye fase de grupos ni eliminatorias previas).
- "rank_diff" usa un ranking HISTÓRICO derivado solo de partidos anteriores a
  cada partido (Elo clásico: base 1500, K=32, sin ventaja de localía). NO usa
  el ranking FIFA 2026 (eso sería leakage: información futura sobre el pasado).
  Los equipos sin historial reciben un rango neutral ("__neutral__" en team_rank).
- Confederaciones desconocidas = "UNKNOWN" (antes se asumía UEFA por defecto).
- Split TEMPORAL: entrena con 2014+2018 y evalúa en 2022 (año más reciente);
  nunca mezcla aleatoria entre años.
- Evaluación: Brier multiclase, log-loss, precisión y calibración (ECE, 5 bins)
  del modelo RandomForest y de un baseline Poisson simple, en
  data/export/predictor_metrics.json. Con n=48 las métricas son indicativas,
  no garantías. Uso exploratorio, no para apuestas.
"""

import json
import math
import sqlite3
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, log_loss
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import LabelEncoder

BASE = Path(__file__).parent.parent
WC_DB = BASE / "data" / "worldcup.db"
HIST_DB = BASE / "data" / "historical.db"
METRICS_PATH = BASE / "data" / "export" / "predictor_metrics.json"

UNKNOWN_CONF = "UNKNOWN"
NEUTRAL_KEY = "__neutral__"
ELO_BASE = 1500.0
ELO_K = 32.0
CLASSES = ["home_win", "draw", "away_win"]


def _conn(db):
    return sqlite3.connect(str(db))


def _elo_expected(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


def _label(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "home_win"
    if away_score > home_score:
        return "away_win"
    return "draw"


def _historical_context(matches: pd.DataFrame) -> tuple[list[dict], dict, dict]:
    """Procesa los partidos en orden cronológico y calcula, para cada uno, el
    Elo y el ranking previos al partido (solo información pasada).

    Devuelve (contextos, elo_final, rank_final). El ranking de un equipo es la
    posición de competición (1 = mejor) entre los equipos que ya tienen
    partidos; un equipo sin historial se sitúa en el Elo base (1500), es decir,
    en mitad de tabla, y su rango se deriva del campo establecido.
    """
    elo: dict[str, float] = {}
    played: set[str] = set()
    ctxs: list[dict] = []
    for _, r in matches.iterrows():
        h, a = r["home"], r["away"]
        eh = elo.get(h, ELO_BASE)
        ea = elo.get(a, ELO_BASE)
        rank_h = 1 + sum(1 for t in played if elo[t] > eh)
        rank_a = 1 + sum(1 for t in played if elo[t] > ea)
        ctxs.append(
            {"elo_home": eh, "elo_away": ea, "rank_home": rank_h, "rank_away": rank_a}
        )
        sh = (
            1.0
            if r["label"] == "home_win"
            else (0.0 if r["label"] == "away_win" else 0.5)
        )
        exp_h = _elo_expected(eh, ea)
        elo[h] = eh + ELO_K * (sh - exp_h)
        elo[a] = ea + ELO_K * ((1.0 - sh) - (1.0 - exp_h))
        played.add(h)
        played.add(a)
    rank_final = {t: 1 + sum(1 for u in played if elo[u] > elo[t]) for t in played}
    neutral = 1 + sum(1 for t in played if elo[t] > ELO_BASE)
    rank_final[NEUTRAL_KEY] = neutral
    return ctxs, elo, rank_final


def _historical_confs(hist_db) -> dict[str, str]:
    """Confederación por equipo tomada del histórico (del año del Mundial),
    no del torneo 2026. Última aparición gana."""
    teams = pd.read_sql("SELECT wc_id, name, confederation FROM teams", hist_db)
    cups = pd.read_sql("SELECT wc_id, year FROM world_cups", hist_db)
    year_of = dict(zip(cups["wc_id"], cups["year"]))
    conf: dict[str, str] = {}
    best_year: dict[str, int] = {}
    for _, t in teams.iterrows():
        y = year_of.get(t["wc_id"], 0)
        if y >= best_year.get(t["name"], -1):
            best_year[t["name"]] = y
            conf[t["name"]] = t["confederation"] or UNKNOWN_CONF
    return conf


def load_training_data():
    conn = _conn(HIST_DB)
    matches = pd.read_sql("SELECT * FROM matches", conn)
    hist_confs = _historical_confs(conn)
    conn.close()

    matches = matches.rename(columns={"home_team": "home", "away_team": "away"})
    matches["label"] = matches.apply(
        lambda r: _label(r["home_score"], r["away_score"]), axis=1
    )
    matches = matches.sort_values(["date", "id"]).reset_index(drop=True)
    matches["year"] = matches["date"].str.slice(0, 4).astype(int)

    # ranking histórico por año, sin leakage del futuro (se recalcula por año)
    ctxs, _elo_final, team_rank = _historical_context(matches)

    all_teams = pd.unique(pd.concat([matches["home"], matches["away"]]))
    team_stats = {t: {"wins": 0, "total": 0, "gf": 0, "ga": 0} for t in all_teams}

    rows = []
    for (_, r), ctx in zip(matches.iterrows(), ctxs):
        h, a = r["home"], r["away"]
        hs = team_stats.setdefault(h, {"wins": 0, "total": 0, "gf": 0, "ga": 0})
        aws = team_stats.setdefault(a, {"wins": 0, "total": 0, "gf": 0, "ga": 0})

        is_knockout = 1 if r["round"] != "Group Stage" else 0

        rows.append(
            {
                "home": h,
                "away": a,
                "date": r["date"],
                "year": r["year"],
                "is_knockout": is_knockout,
                "home_win_rate": hs["wins"] / max(hs["total"], 1),
                "away_win_rate": aws["wins"] / max(aws["total"], 1),
                "home_avg_gf": hs["gf"] / max(hs["total"], 1),
                "away_avg_gf": aws["gf"] / max(aws["total"], 1),
                "home_avg_ga": hs["ga"] / max(hs["total"], 1),
                "away_avg_ga": aws["ga"] / max(aws["total"], 1),
                "home_conf": hist_confs.get(h, UNKNOWN_CONF),
                "away_conf": hist_confs.get(a, UNKNOWN_CONF),
                # Ranking histórico previo al partido (sin leakage).
                "rank_diff": ctx["rank_home"] - ctx["rank_away"],
                "home_score": int(r["home_score"]),
                "away_score": int(r["away_score"]),
                "label": r["label"],
            }
        )

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

    return pd.DataFrame(rows), hist_confs, team_rank


FEATURES = [
    "is_knockout",
    "home_win_rate",
    "away_win_rate",
    "home_avg_gf",
    "away_avg_gf",
    "home_avg_ga",
    "away_avg_ga",
    "home_conf_enc",
    "away_conf_enc",
    "rank_diff",
]


def _fit_encoders(df: pd.DataFrame) -> tuple[LabelEncoder, LabelEncoder]:
    le_home = LabelEncoder()
    le_away = LabelEncoder()
    # UNKNOWN siempre presente para no asumir ninguna confederación real.
    le_home.fit(sorted(set(df["home_conf"]) | {UNKNOWN_CONF}))
    le_away.fit(sorted(set(df["away_conf"]) | {UNKNOWN_CONF}))
    return le_home, le_away


def _encode_conf(le: LabelEncoder, conf: str) -> int:
    if conf in le.classes_:
        return int(le.transform([conf])[0])
    return int(le.transform([UNKNOWN_CONF])[0])


def _temporal_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split temporal: el año más reciente queda como test; nada de aleatoriedad."""
    max_year = int(df["year"].max())
    train = df[df["year"] < max_year].reset_index(drop=True)
    test = df[df["year"] == max_year].reset_index(drop=True)
    return train, test


def _make_model() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )


def train_model(cv_folds: int = 5) -> tuple:
    df, team_conf, team_rank = load_training_data()

    le_home, le_away = _fit_encoders(df)
    df["home_conf_enc"] = df["home_conf"].map(lambda c: _encode_conf(le_home, c))
    df["away_conf_enc"] = df["away_conf"].map(lambda c: _encode_conf(le_away, c))

    X = df[FEATURES].fillna(0)
    y = df["label"]

    train_mask = df["year"] < int(df["year"].max())
    X_train, X_test = X[train_mask], X[~train_mask]
    y_train, y_test = y[train_mask], y[~train_mask]

    model = _make_model()
    model.fit(X_train, y_train)

    # CV solo como diagnóstico del train; con series temporales no se mezclan años.
    min_class_count = y_train.value_counts().min()
    cv_folds_actual = min(cv_folds, max(min_class_count, 1), max(len(X_train) // 4, 1))
    if cv_folds_actual >= 2 and y_train.nunique() >= 2:
        cv = TimeSeriesSplit(n_splits=cv_folds_actual)
        cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="accuracy")
        print(
            f"CV Accuracy temporal ({cv_folds_actual}-fold): "
            f"{cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})"
        )
    else:
        print("Skipping CV: insufficient samples per class")

    accuracy = model.score(X_test, y_test)
    print(
        f"Test Accuracy (año {int(df['year'].max())}, split temporal): {accuracy:.3f}"
    )

    y_pred = model.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    importance = pd.DataFrame(
        {"feature": FEATURES, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)
    print("\nFeature Importance:")
    print(importance.to_string(index=False))

    return model, FEATURES, le_home, le_away, team_conf, team_rank


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
                if (is_home and r["home_score"] > r["away_score"]) or (
                    not is_home and r["away_score"] > r["home_score"]
                ):
                    wins += 1
        return {
            "wins": wins,
            "total": total,
            "gf": gf / max(total, 1),
            "ga": ga / max(total, 1),
            "win_rate": wins / max(total, 1),
        }

    hs = _stats(home_team)
    aws = _stats(away_team)

    # Confederación del torneo 2026 solo para mostrar/encoding; desconocida = UNKNOWN.
    wc_teams = get_all_teams()
    wc_confs = {t["name"]: t["confederation"] for t in wc_teams}
    ranks_2026 = {t["name"]: t["fifa_ranking"] for t in wc_teams}
    home_conf = wc_confs.get(home_team, UNKNOWN_CONF) or UNKNOWN_CONF
    away_conf = wc_confs.get(away_team, UNKNOWN_CONF) or UNKNOWN_CONF
    hc_enc = _encode_conf(le_home, home_conf)
    ac_enc = _encode_conf(le_away, away_conf)

    neutral_rank = team_rank.get(NEUTRAL_KEY, max(team_rank.values(), default=1))
    home_rank = team_rank.get(home_team, neutral_rank)
    away_rank = team_rank.get(away_team, neutral_rank)

    X_pred = pd.DataFrame(
        [
            {
                "is_knockout": 0,
                "home_win_rate": hs["win_rate"],
                "away_win_rate": aws["win_rate"],
                "home_avg_gf": hs["gf"],
                "away_avg_gf": aws["gf"],
                "home_avg_ga": hs["ga"],
                "away_avg_ga": aws["ga"],
                "home_conf_enc": hc_enc,
                "away_conf_enc": ac_enc,
                "rank_diff": home_rank - away_rank,
            }
        ]
    )[features]

    proba = model.predict_proba(X_pred)[0]
    classes = model.classes_.tolist()

    # fifa_ranking (2026) es solo informativo; el modelo NO lo usa (sin leakage).
    result = {
        "home_team": home_team,
        "away_team": away_team,
        "probabilities": {c: round(float(p) * 100, 1) for c, p in zip(classes, proba)},
        "home_stats": {
            "fifa_ranking": ranks_2026.get(home_team, "N/A"),
            "confederation": home_conf,
            "wc_matches": hs["total"],
            "wc_win_rate": round(hs["win_rate"] * 100, 1),
        },
        "away_stats": {
            "fifa_ranking": ranks_2026.get(away_team, "N/A"),
            "confederation": away_conf,
            "wc_matches": aws["total"],
            "wc_win_rate": round(aws["win_rate"] * 100, 1),
        },
    }
    return result


def get_all_teams():
    conn = _conn(WC_DB)
    teams = pd.read_sql(
        "SELECT name, fifa_ranking, confederation FROM teams ORDER BY fifa_ranking",
        conn,
    )
    conn.close()
    return teams.to_dict("records")


def _calibration(y_true, probs, classes, n_bins: int = 5) -> dict:
    """Calibración top-label: confianza (prob. de la clase predicha) vs exactitud."""
    idx = {c: i for i, c in enumerate(classes)}
    pred_idx = probs.argmax(axis=1)
    conf = probs[range(len(probs)), pred_idx]
    correct = np.array([idx[label] for label in y_true]) == pred_idx
    bins = {}
    ece = 0.0
    for b in range(n_bins):
        lo, hi = b / n_bins, (b + 1) / n_bins
        mask = (conf >= lo) & (conf < hi if b < n_bins - 1 else conf <= hi)
        n = int(mask.sum())
        if n == 0:
            bins[f"{lo:.1f}-{hi:.1f}"] = {"n": 0, "mean_conf": None, "acc": None}
            continue
        mean_conf = float(conf[mask].mean())
        acc = float(correct[mask].mean())
        ece += (n / len(probs)) * abs(acc - mean_conf)
        bins[f"{lo:.1f}-{hi:.1f}"] = {
            "n": n,
            "mean_conf": round(mean_conf, 4),
            "acc": round(acc, 4),
        }
    return {"bins": bins, "ece": round(float(ece), 4)}


def _multiclass_brier(y_true, probs, classes) -> float:
    idx = {c: i for i, c in enumerate(classes)}
    y_onehot = np.zeros_like(probs)
    for i, label in enumerate(y_true):
        y_onehot[i, idx[label]] = 1.0
    return float(np.mean(np.sum((probs - y_onehot) ** 2, axis=1)))


def _align_proba(model_proba, model_classes) -> np.ndarray:
    """Alinea las probabilidades del modelo al orden CLASSES (faltantes = 0)."""
    aligned = np.zeros((model_proba.shape[0], len(CLASSES)))
    for j, c in enumerate(model_classes):
        aligned[:, CLASSES.index(c)] = model_proba[:, j]
    return aligned


def _poisson_baseline(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Baseline Poisson simple: tasas de goles a favor/en contra del train,
    con shrinkage hacia la media global (w=3) para no confiar en 1 partido."""
    w = 3.0
    global_gf = float(pd.concat([train["home_score"], train["away_score"]]).mean())
    stats: dict[str, dict] = {}

    def _touch(team, gf, ga):
        s = stats.setdefault(team, {"gf": 0.0, "ga": 0.0, "n": 0})
        s["gf"] += gf
        s["ga"] += ga
        s["n"] += 1

    for _, r in train.iterrows():
        _touch(r["home"], r["home_score"], r["away_score"])
        _touch(r["away"], r["away_score"], r["home_score"])

    def _rates(team):
        s = stats.get(team)
        if not s:
            return global_gf, global_gf
        lam_for = (s["gf"] + w * global_gf) / (s["n"] + w)
        lam_against = (s["ga"] + w * global_gf) / (s["n"] + w)
        return lam_for, lam_against

    max_goals = 8
    probs = []
    for _, r in test.iterrows():
        lam_for_h, lam_against_h = _rates(r["home"])
        lam_for_a, lam_against_a = _rates(r["away"])
        # Fuerza relativa: ataque propio x debilidad defensiva del rival.
        lam_home = max(lam_for_h * lam_against_a / global_gf, 0.05)
        lam_away = max(lam_for_a * lam_against_h / global_gf, 0.05)
        grid = []
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                p = math.exp(-lam_home) * lam_home**i / math.factorial(i)
                p *= math.exp(-lam_away) * lam_away**j / math.factorial(j)
                grid.append((i, j, p))
        total = sum(p for _, _, p in grid)
        p_home = sum(p for i, j, p in grid if i > j) / total
        p_draw = sum(p for i, j, p in grid if i == j) / total
        p_away = sum(p for i, j, p in grid if i < j) / total
        probs.append([p_home, p_draw, p_away])
    return np.array(probs)


def _metrics_block(y_true, probs) -> dict:
    classes = list(CLASSES)
    pred_labels = [CLASSES[p] for p in probs.argmax(axis=1)]
    acc = float(np.mean([p == t for p, t in zip(pred_labels, y_true)]))
    # clip manual (la versión de sklearn instalada no acepta clip= en log_loss).
    # Las columnas de probs ya están alineadas a CLASSES vía _align_proba.
    clipped = np.clip(probs, 1e-6, 1.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        ll = float(log_loss(y_true, clipped, labels=classes))
    return {
        "brier_multiclass": round(_multiclass_brier(y_true, probs, classes), 4),
        "log_loss": round(ll, 4),
        "accuracy": round(acc, 4),
        "calibration": _calibration(y_true, probs, classes),
    }


def evaluate_predictor(output_path: Path | None = None) -> dict:
    """Entrena con años < máx y evalúa el año más reciente: modelo vs baseline."""
    if output_path is None:
        output_path = METRICS_PATH

    df, _team_conf, _team_rank = load_training_data()
    le_home, le_away = _fit_encoders(df)
    df["home_conf_enc"] = df["home_conf"].map(lambda c: _encode_conf(le_home, c))
    df["away_conf_enc"] = df["away_conf"].map(lambda c: _encode_conf(le_away, c))

    train, test = _temporal_split(df)
    model = _make_model()
    model.fit(train[FEATURES].fillna(0), train["label"])

    y_true = test["label"].tolist()
    model_probs = _align_proba(
        model.predict_proba(test[FEATURES].fillna(0)), model.classes_
    )
    baseline_probs = _poisson_baseline(train, test)

    results = {
        "n_total": int(len(df)),
        "split": {
            "train_years": sorted(train["year"].unique().astype(int).tolist()),
            "test_years": sorted(test["year"].unique().astype(int).tolist()),
            "n_train": int(len(train)),
            "n_test": int(len(test)),
            "kind": "temporal",
        },
        "model_random_forest": _metrics_block(y_true, model_probs),
        "baseline_poisson": _metrics_block(y_true, baseline_probs),
        "classes": CLASSES,
        "note": (
            "Evaluación sobre el año más reciente (2022). n pequeño: métricas "
            "indicativas, no garantías. Baseline Poisson con shrinkage w=3."
        ),
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[-evaluate] train={results['split']} test n={len(test)}")
    for name in ("model_random_forest", "baseline_poisson"):
        m = results[name]
        print(
            f"[evaluate] {name}: brier={m['brier_multiclass']} "
            f"logloss={m['log_loss']} acc={m['accuracy']} ece={m['calibration']['ece']}"
        )
    return results


def export_predictions(output_path=None):
    if output_path is None:
        output_path = BASE / "data" / "export" / "predictions.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    teams = [t["name"] for t in get_all_teams()[:16]]
    predictions = []
    for i, h in enumerate(teams):
        for a in teams[i + 1 :]:
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
    evaluate_predictor()
