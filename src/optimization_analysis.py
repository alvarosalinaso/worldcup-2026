"""
Optimizacion de asignacion de partidos a sedes.
Analisis de capacidad vs demanda y asignacion optima.
"""

import json
from pathlib import Path

try:
    import numpy as np
    import pandas as pd

    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def run_optimization(
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

    # Capacity utilization analysis
    if len(num_cols) >= 2:
        capacity_col = num_cols[0]
        demand_col = num_cols[1]
        df["utilization_pct"] = (df[demand_col] / df[capacity_col] * 100).round(1)
        df["surplus"] = df[capacity_col] - df[demand_col]

        # Classification
        df["status"] = df["utilization_pct"].apply(
            lambda x: (
                "OPTIMO"
                if 85 <= x <= 100
                else "SUBUTILIZADO"
                if x < 85
                else "SOBREDEMANDA"
            )
        )

    results = {
        "n_sedes": len(df),
        "utilization_stats": {
            "mean": round(df["utilization_pct"].mean(), 1)
            if "utilization_pct" in df.columns
            else 0,
            "min": round(df["utilization_pct"].min(), 1)
            if "utilization_pct" in df.columns
            else 0,
            "max": round(df["utilization_pct"].max(), 1)
            if "utilization_pct" in df.columns
            else 0,
        },
        "status_distribution": df["status"].value_counts().to_dict()
        if "status" in df.columns
        else {},
        "recommendations": [],
    }

    # Generate recommendations
    if "status" in df.columns:
        underutilized = df[df["status"] == "SUBUTILIZADO"]
        overdemand = df[df["status"] == "SOBREDEMANDA"]

        if len(underutilized) > 0:
            results["recommendations"].append(
                f"{len(underutilized)} sedes subutilizadas - considerar redistribucion"
            )
        if len(overdemand) > 0:
            results["recommendations"].append(
                f"{len(overdemand)} sedes sobredemandadas - anadir capacidad o sesiones"
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "optimization_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[OPT] Utilizacion media: {results['utilization_stats']['mean']}%")
    return results


if __name__ == "__main__":
    run_optimization()
