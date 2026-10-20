"""
Forecasting de asistencia para World Cup 2026.
ARIMA sobre la serie historica de asistencia POR MUNDIAL (world_cups).
Solo tiene sentido predecir una serie temporal real con eje temporal; por eso
NO se aplica ARIMA a columnas estaticas (capacity, lat, lon).
"""

import json
import sqlite3
from pathlib import Path

try:
    import pandas as pd
    from statsmodels.tsa.arima.model import ARIMA

    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def _series_asistencia_historica(hist_db: Path) -> pd.Series:
    """Asistencia total por anio de mundial desde historical.db (2014-2022)."""
    if not hist_db.exists():
        return pd.Series(dtype=float)
    conn = sqlite3.connect(hist_db)
    df = pd.read_sql(
        "SELECT year, total_attendance FROM world_cups ORDER BY year", conn
    )
    conn.close()
    if df.empty:
        return pd.Series(dtype=float)
    return pd.Series(df["total_attendance"].values, index=df["year"].astype(int))


def run_forecasting(
    output_dir: Path = Path("data/export"),
    hist_db: Path = Path("data/historical.db"),
) -> dict:
    if not AVAILABLE:
        print("[FORECAST] statsmodels no instalado")
        return {}

    ts = _series_asistencia_historica(hist_db).dropna()
    # ARIMA necesita historia suficiente; con <5 observaciones es insensato.
    if len(ts) < 5:
        print(
            f"[FORECAST] solo {len(ts)} observaciones historicas de asistencia; "
            "no hay serie suficiente para ARIMA (se omiten predicciones)"
        )
        results = {
            "note": (
                "Sin forecast: la asistencia historica por mundial tiene "
                f"{len(ts)} observaciones, insuficiente para ARIMA."
            ),
            "series": {int(k): int(v) for k, v in ts.items()},
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "forecasting_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        return results

    try:
        fit = ARIMA(ts.values, order=(1, 1, 0)).fit()
        forecast = fit.forecast(steps=1)
        results = {
            "series": {int(k): int(v) for k, v in ts.items()},
            "forecast_next_year": round(float(forecast[0]), 2),
            "aic": round(float(fit.aic), 2),
            "note": "Forecast ARIMA(1,1,0) sobre asistencia por mundial.",
        }
        print(f"[FORECAST] asistencia proximo mundial ~ {forecast[0]:,.0f}")
    except Exception as e:
        print(f"[FORECAST] error: {e}")
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "forecasting_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results


if __name__ == "__main__":
    run_forecasting()
