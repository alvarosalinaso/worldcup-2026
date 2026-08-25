"""
Forecasting de asistencia y demanda para World Cup 2026.
ARIMA + Holt-Winters para predecir patron de asistencia.
"""
import json
from pathlib import Path

try:
    import pandas as pd
    import numpy as np
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def run_forecasting(data_dir: Path = Path("."), output_dir: Path = Path("data/export")) -> dict:
    if not AVAILABLE:
        print("[FORECAST] statsmodels no instalado")
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
        ts = df[col].dropna()
        if len(ts) < 5:
            continue
        try:
            model = ARIMA(ts.values, order=(1, 1, 0))
            fit = model.fit()
            forecast = fit.forecast(steps=3)
            results[col] = {
                "forecast_next_3": [round(float(v), 2) for v in forecast],
                "aic": round(float(fit.aic), 2),
                "mean": round(float(ts.mean()), 2),
            }
            print(f"[FORECAST] {col}: mean={ts.mean():.1f}, forecast={[round(float(v), 1) for v in forecast]}")
        except Exception as e:
            print(f"[FORECAST] {col} error: {e}")

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "forecasting_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results


if __name__ == "__main__":
    run_forecasting()
