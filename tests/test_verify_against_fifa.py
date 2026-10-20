"""Tests para verify_against_fifa (contraste A-3, sin red)."""

from src.verify_against_fifa import (
    compare,
    load_repo_knockout,
    load_repo_totals,
    normalize_team,
    render_ledger,
)


def _fifa_match(no, h, a, hs, ascore, stage="Knockout"):
    return {
        "MatchNumber": no,
        "IdMatch": f"4000{no}",
        "LocalDate": "2026-07-19T15:00:00Z",
        "Attendance": "80000",
        "StageName": [{"Locale": "en-GB", "Description": stage}],
        "Home": {
            "TeamName": [{"Locale": "en-GB", "Description": h}],
            "Score": hs,
            "HomeTeamPenaltyScore": None,
        },
        "Away": {
            "TeamName": [{"Locale": "en-GB", "Description": a}],
            "Score": ascore,
            "AwayTeamPenaltyScore": None,
        },
        "Stadium": {"Name": [{"Locale": "en-GB", "Description": "Test Stadium"}]},
    }


def _repo_row(home, away, hs, ascore):
    return {
        "home_team": home,
        "away_team": away,
        "home_score": hs,
        "away_score": ascore,
        "pens_home": None,
        "pens_away": None,
    }


def test_normalize_team_aliases():
    assert normalize_team("Côte d'Ivoire") == "Ivory Coast"
    assert normalize_team("Congo DR") == "DR Congo"
    assert normalize_team("Spain") == "Spain"


def test_compare_no_discrepancies():
    fifa = [
        _fifa_match(103, "France", "England", 4, 6),
        _fifa_match(104, "Spain", "Argentina", 1, 0),
    ]
    repo_ko = {
        103: _repo_row("France", "England", 4, 6),
        104: _repo_row("Spain", "Argentina", 1, 0),
    }
    result = compare(fifa, repo_ko, {"matches": 2, "goals": 11}, expected_matches=2)
    assert result["discrepancies"] == []
    assert result["knockout_checked"] == 2
    assert result["final"]["fifa"].startswith("Spain 1-0")
    assert result["third_place"]["repo"] == "France 4-6 England"


def test_compare_reports_score_discrepancy():
    fifa = [_fifa_match(104, "Spain", "Argentina", 2, 0)]
    repo_ko = {104: _repo_row("Spain", "Argentina", 1, 0)}
    result = compare(fifa, repo_ko, {"matches": 1, "goals": 2}, expected_matches=1)
    assert any("marcador" in d for d in result["discrepancies"])


def test_compare_reports_team_discrepancy_with_aliases():
    fifa = [_fifa_match(78, "Côte d'Ivoire", "Norway", 1, 2)]
    repo_ko = {78: _repo_row("Ivory Coast", "Norway", 1, 2)}
    result = compare(fifa, repo_ko, {"matches": 1, "goals": 3}, expected_matches=1)
    assert result["discrepancies"] == []

    repo_bad = {78: _repo_row("Ivory Coast", "Sweden", 1, 2)}
    result_bad = compare(fifa, repo_bad, {"matches": 1, "goals": 3}, expected_matches=1)
    assert any("equipos" in d for d in result_bad["discrepancies"])


def test_compare_totals_and_missing_match():
    fifa = [_fifa_match(104, "Spain", "Argentina", 1, 0)]
    repo_ko = {
        104: _repo_row("Spain", "Argentina", 1, 0),
        90: _repo_row("A", "B", 1, 0),
    }
    result = compare(fifa, repo_ko, {"matches": 104, "goals": 10})
    assert any("partidos" in d for d in result["discrepancies"])
    assert any("match 90" in d for d in result["discrepancies"])
    assert any("goles" in d for d in result["discrepancies"])


def test_render_ledger_contains_required_fields():
    fifa = [
        _fifa_match(103, "France", "England", 4, 6),
        _fifa_match(104, "Spain", "Argentina", 1, 0),
    ]
    repo_ko = {
        103: _repo_row("France", "England", 4, 6),
        104: _repo_row("Spain", "Argentina", 1, 0),
    }
    comparison = compare(fifa, repo_ko, {"matches": 2, "goals": 11}, expected_matches=2)
    text = render_ledger(comparison, "2026-10-19")
    assert "Fecha de acceso: 2026-10-19" in text
    assert "api.fifa.com" in text
    assert "¿Coincide?" in text
    assert "Spain 1-0 Argentina" in text


def test_committed_ledger_exists_and_cites_fifa():
    from pathlib import Path

    ledger = Path(__file__).resolve().parent.parent / "data" / "contrast_ledger.md"
    assert ledger.exists()
    text = ledger.read_text(encoding="utf-8")
    assert "api.fifa.com" in text
    assert "Final (match 104)" in text
    assert "3er lugar (match 103)" in text
    assert "400021543" in text


def test_load_repo_helpers_on_real_db():
    from pathlib import Path

    db = Path(__file__).resolve().parent.parent / "data" / "worldcup_real.db"
    ko = load_repo_knockout(db)
    totals = load_repo_totals(db)
    assert len(ko) == 32
    assert 104 in ko and 103 in ko
    assert totals["matches"] == 104
    assert totals["goals"] == 308
