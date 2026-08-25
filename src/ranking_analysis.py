"""
Ranking estadistico de sedes World Cup 2026.
Scoring compuesto con normalizacion y ponderacion.
"""

import json
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
    from scipy import stats

    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def run_ranking(
    data_dir: Path = Path("."), output_dir: Path = Path("data/export")
) -> dict:
    if not AVAILABLE:
        return {}

    csv_file = data_dir / "dw_asistencia_sedes.csv"
    if not csv_file.exists():
        return {}

    df = pd.read_csv(csv_file, encoding="utf-8")
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) < 2:
        return {}

    # Z-score normalization
    df_z = pd.DataFrame()
    for col in num_cols:
        df_z[col + "_z"] = (
            (df[col] - df[col].mean()) / df[col].std() if df[col].std() > 0 else 0
        )

    # Composite score (equal weights)
    df_z["composite_score"] = df_z.mean(axis=1)
    df_z["rank"] = df_z["composite_score"].rank(ascending=False).astype(int)

    # Add labels
    label_col = (
        "city"
        if "city" in df.columns
        else ("sede" if "sede" in df.columns else df.columns[0])
    )
    df_z["sede"] = df[label_col].values

    # Percentile ranking
    df_z["percentile"] = stats.percentileofscore(
        df_z["composite_score"], df_z["composite_score"]
    )

    results = {
        "ranking": df_z.sort_values("rank")[
            ["sede", "rank", "composite_score", "percentile"]
        ].to_dict(orient="records"),
        "n_sedes": len(df),
        "metrics_used": num_cols,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "ranking_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[RANKING] Top 3: {results['ranking'][:3]}")
    return results


if __name__ == "__main__":
    run_ranking()
