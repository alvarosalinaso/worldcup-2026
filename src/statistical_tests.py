"""Tests estadisticos para World Cup 2026."""

import json
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


def run_statistical_tests(
    data_dir: Path = Path("."), output_dir: Path = Path("data/export")
) -> dict:
    if not SCIPY_AVAILABLE:
        return {}

    csv_file = data_dir / "dw_asistencia_sedes.csv"
    if not csv_file.exists():
        print("[STATS] dw_asistencia_sedes.csv no encontrado")
        return {}

    df = pd.read_csv(csv_file, encoding="utf-8")
    results = {}

    # Find numeric columns for correlation
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) >= 2:
        r, p = stats.pearsonr(df[num_cols[0]].dropna(), df[num_cols[1]].dropna())
        results["pearson_capacity_vs_attendance"] = {
            "test": "Pearson correlation",
            "variables": [num_cols[0], num_cols[1]],
            "r": round(r, 4),
            "p_value": round(p, 6),
            "significant": p < 0.05,
        }
        print(f"[STATS] Pearson: r={r:.3f}, p={p:.4f}")

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "statistical_tests.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results
