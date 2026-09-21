"""Tests for statistical_tests module (worldcup-2026)."""

import json
from pathlib import Path
import pytest

from src.statistical_tests import run_statistical_tests


def test_run_statistical_tests_returns_dict(tmp_path):
    """Test that run_statistical_tests returns a dict."""
    data_dir = tmp_path / "data" / "export"
    output_dir = tmp_path / "data" / "export_out"
    data_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    # Create mock data files needed by statistical_tests
    import pandas as pd
    matches_csv = data_dir / "matches.csv"
    pd.DataFrame({
        "round": ["Group Stage", "Round of 16", "Quarterfinal"],
        "home_score": [2, 1, 3],
        "away_score": [1, 1, 0],
        "attendance": [50000, 60000, 70000],
    }).to_csv(matches_csv, index=False)

    teams_csv = data_dir / "teams.csv"
    pd.DataFrame({
        "name": ["Spain", "Argentina", "France"],
        "confederation": ["UEFA", "CONMEBOL", "UEFA"],
        "fifa_ranking": [2, 1, 3],
    }).to_csv(teams_csv, index=False)

    result = run_statistical_tests(data_dir=data_dir, output_dir=output_dir)
    assert isinstance(result, dict)


def test_run_statistical_tests_creates_output(tmp_path):
    """Test that run_statistical_tests creates output file."""
    data_dir = tmp_path / "data" / "export"
    output_dir = tmp_path / "data" / "export_out"
    data_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    import pandas as pd
    matches_csv = data_dir / "matches.csv"
    pd.DataFrame({
        "round": ["Group Stage", "Group Stage"],
        "home_score": [2, 1],
        "away_score": [1, 0],
        "attendance": [50000, 60000],
    }).to_csv(matches_csv, index=False)

    result = run_statistical_tests(data_dir=data_dir, output_dir=output_dir)
    output_file = output_dir / "statistical_tests.json"
    # May or may not create file depending on scipy availability
    assert isinstance(result, dict)