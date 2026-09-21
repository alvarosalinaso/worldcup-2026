"""Tests for clustering_analysis module (worldcup-2026)."""

import json
from pathlib import Path
import pytest

from src.clustering_analysis import run_clustering


def test_run_clustering_returns_dict(tmp_path):
    """Test that run_clustering returns a dict."""
    data_dir = tmp_path / "data" / "export"
    output_dir = tmp_path / "data" / "export_out"
    data_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    import pandas as pd
    matches_csv = data_dir / "matches.csv"
    pd.DataFrame({
        "stadium_id": [1, 2, 3],
        "capacity": [80000, 70000, 60000],
        "attendance": [75000, 65000, 55000],
        "region": ["Central", "Eastern", "Western"],
    }).to_csv(matches_csv, index=False)

    stadiums_csv = data_dir / "stadiums.csv"
    pd.DataFrame({
        "stadium_id": [1, 2, 3],
        "name": ["Stadium A", "Stadium B", "Stadium C"],
        "capacity": [80000, 70000, 60000],
    }).to_csv(stadiums_csv, index=False)

    result = run_clustering(data_dir=data_dir, output_dir=output_dir)
    assert isinstance(result, dict)


def test_run_clustering_no_data(tmp_path):
    """Test run_clustering with missing data."""
    data_dir = tmp_path / "data" / "export"
    output_dir = tmp_path / "data" / "export_out"
    data_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    result = run_clustering(data_dir=data_dir, output_dir=output_dir)
    assert isinstance(result, dict)
    assert result == {}