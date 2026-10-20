"""Tests estadisticos para World Cup 2026."""

import json
from pathlib import Path

try:
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

    # Correlacion explicita capacidad vs asistencia (mismas filas en ambos
    # vectores: dropna alineado, no dropna independiente que desalinea).
    if {"capacity", "attendance"} <= set(df.columns):
        clean = df[["capacity", "attendance"]].dropna()
        if len(clean) >= 3:
            r, p = stats.pearsonr(clean["capacity"], clean["attendance"])
            results["pearson_capacity_vs_attendance"] = {
                "test": "Pearson correlation",
                "variables": ["capacity", "attendance"],
                "n": int(len(clean)),
                "r": round(r, 4),
                "p_value": round(p, 6),
                "significant": bool(p < 0.05),
                "note": (
                    "n muy pequeno (sedes del Mundial 2026): el p-valor es "
                    "indicativo, no concluyente."
                ),
            }
            print(
                f"[STATS] Pearson capacity~attendance: r={r:.3f}, p={p:.4f}, n={len(clean)}"
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "statistical_tests.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results
