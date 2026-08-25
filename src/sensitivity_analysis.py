"""
Analisis de sensibilidad — Impacto de variaciones en parametros clave.
Monte Carlo simulation para escenarios de asistencia.
"""

import json
from pathlib import Path

try:
    import numpy as np
    import pandas as pd

    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def run_sensitivity(
    data_dir: Path = Path("."),
    output_dir: Path = Path("data/export"),
    n_simulations: int = 1000,
) -> dict:
    if not AVAILABLE:
        return {}

    csv_file = data_dir / "dw_asistencia_sedes.csv"
    if not csv_file.exists():
        return {}

    df = pd.read_csv(csv_file, encoding="utf-8")
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not num_cols:
        return {}

    results = {}
    for col in num_cols:
        values = df[col].dropna()
        if len(values) < 3:
            continue

        mean_val = values.mean()
        std_val = values.std()

        # Monte Carlo simulation
        simulations = np.random.normal(mean_val, std_val * 0.15, n_simulations)

        results[col] = {
            "baseline": round(float(mean_val), 2),
            "std": round(float(std_val), 2),
            "simulation_mean": round(float(simulations.mean()), 2),
            "simulation_std": round(float(simulations.std()), 2),
            "p5": round(float(np.percentile(simulations, 5)), 2),
            "p25": round(float(np.percentile(simulations, 25)), 2),
            "p75": round(float(np.percentile(simulations, 75)), 2),
            "p95": round(float(np.percentile(simulations, 95)), 2),
            "probability_above_baseline": round(
                float(np.mean(simulations > mean_val)), 3
            ),
        }
        print(
            f"[SENS] {col}: baseline={mean_val:.1f}, P(above)={results[col]['probability_above_baseline']:.2%}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "sensitivity_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results


if __name__ == "__main__":
    run_sensitivity()
