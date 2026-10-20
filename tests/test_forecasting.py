"""Tests for forecasting module (worldcup-2026)."""

import sqlite3

from src.forecasting import run_forecasting


def _make_hist_db(path, years):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE world_cups (year INTEGER, total_attendance INTEGER)")
    for y, att in years:
        conn.execute("INSERT INTO world_cups VALUES (?, ?)", (y, att))
    conn.commit()
    conn.close()


def test_forecasting_no_historical_db(tmp_path):
    """Sin historical.db no hay serie: devuelve nota, no inventa forecast."""
    out = tmp_path / "export_out"
    missing = tmp_path / "no_existe.db"

    result = run_forecasting(output_dir=out, hist_db=missing)

    assert isinstance(result, dict)
    assert "note" in result
    assert "forecast_next_year" not in result
    assert (out / "forecasting_results.json").exists()


def test_forecasting_insufficient_series(tmp_path):
    """Con <5 observaciones ARIMA no corre; se documenta y se exporta la serie."""
    hist_db = tmp_path / "historical.db"
    _make_hist_db(hist_db, [(2014, 3386819), (2018, 3031768), (2022, 3404252)])
    out = tmp_path / "export_out"

    result = run_forecasting(output_dir=out, hist_db=hist_db)

    assert "note" in result
    assert "forecast_next_year" not in result
    assert result["series"] == {2014: 3386819, 2018: 3031768, 2022: 3404252}
    assert (out / "forecasting_results.json").exists()


def test_forecasting_with_enough_series(tmp_path):
    """Con >=5 observaciones ARIMA produce un forecast de asistencia."""
    hist_db = tmp_path / "historical.db"
    _make_hist_db(
        hist_db,
        [
            (2002, 2700000),
            (2006, 3359000),
            (2010, 3178000),
            (2014, 3386819),
            (2018, 3031768),
            (2022, 3404252),
        ],
    )
    out = tmp_path / "export_out"

    result = run_forecasting(output_dir=out, hist_db=hist_db)

    assert "forecast_next_year" in result
    assert result["forecast_next_year"] > 0
    assert "aic" in result
    assert len(result["series"]) == 6
