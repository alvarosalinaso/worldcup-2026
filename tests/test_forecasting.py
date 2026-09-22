"""Tests for forecasting module (worldcup-2026)."""

from src.forecasting import run_forecasting


def test_run_forecasting_returns_dict(tmp_path):
    """Test that run_forecasting returns a dict."""
    data_dir = tmp_path / "data" / "export"
    output_dir = tmp_path / "data" / "export_out"
    data_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    import pandas as pd

    matches_csv = data_dir / "matches.csv"
    pd.DataFrame(
        {
            "date": ["2026-06-11", "2026-06-12", "2026-06-13"],
            "attendance": [80000, 75000, 70000],
        }
    ).to_csv(matches_csv, index=False)

    result = run_forecasting(data_dir=data_dir, output_dir=output_dir)
    assert isinstance(result, dict)


def test_run_forecasting_no_data(tmp_path):
    """Test run_forecasting with missing data."""
    data_dir = tmp_path / "data" / "export"
    output_dir = tmp_path / "data" / "export_out"
    data_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    result = run_forecasting(data_dir=data_dir, output_dir=output_dir)
    assert isinstance(result, dict)
    assert result == {}
