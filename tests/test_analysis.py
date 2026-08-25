"""Smoke tests for worldcup-2026."""
import pytest


def test_imports():
    from src.clustering_analysis import run_clustering
    from src.forecasting import run_forecasting
    from src.ranking_analysis import run_ranking
    from src.optimization_analysis import run_optimization
    from src.sensitivity_analysis import run_sensitivity
    from src.statistical_tests import run_statistical_tests
    from src.generate_tables import generate
    assert callable(run_clustering)
    assert callable(run_forecasting)
    assert callable(run_ranking)
    assert callable(run_optimization)
    assert callable(run_sensitivity)
    assert callable(run_statistical_tests)
    assert callable(generate)
