"""Data quality validation for World Cup historical data."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any


def validate_historical_data(db_path: str) -> Dict[str, Any]:
    """
    Validate historical World Cup data quality.
    
    Returns dict with validation results.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "stats": {}
    }
    
    # 1. Check world_cups table
    wc = conn.execute("SELECT * FROM world_cups ORDER BY year").fetchall()
    results["stats"]["world_cups_count"] = len(wc)
    
    for row in wc:
        # Check attendance not negative
        if row["total_attendance"] and row["total_attendance"] < 0:
            results["errors"].append(f"Negative attendance for {row['year']}")
            results["valid"] = False
        
        # Check goals reasonable
        if row["total_goals"] < 100 or row["total_goals"] > 300:
            results["warnings"].append(f"Unusual goal count for {row['year']}: {row['total_goals']}")
    
    # 2. Check matches have valid scores
    matches = conn.execute("""
        SELECT wc_id, round, home_team, away_team, home_score, away_score
        FROM matches
    """).fetchall()
    
    results["stats"]["matches_count"] = len(matches)
    
    for m in matches:
        if m["home_score"] < 0 or m["away_score"] < 0:
            results["errors"].append(f"Negative score: {m['home_team']} vs {m['away_team']}")
            results["valid"] = False
        
        if m["home_score"] > 15 or m["away_score"] > 15:
            results["warnings"].append(f"Unusually high score: {m['home_team']} {m['home_score']}-{m['away_score']} {m['away_team']}")
    
    # 3. Check goals reference valid matches
    goals = conn.execute("SELECT wc_id, match_number, team_name, scorer, goals FROM goals").fetchall()
    results["stats"]["goals_count"] = len(goals)
    
    for g in goals:
        match_exists = conn.execute(
            "SELECT 1 FROM matches WHERE wc_id=? AND match_number=?", 
            (g["wc_id"], g["match_number"])
        ).fetchone()
        if not match_exists:
            results["errors"].append(f"Goal references non-existent match: wc={g['wc_id']}, match={g['match_number']}")
            results["valid"] = False
        
        if g["goals"] < 1 or g["goals"] > 5:
            results["warnings"].append(f"Unusual goal count for {g['scorer']}: {g['goals']}")
    
    # 4. Check group standings consistency
    standings = conn.execute("""
        SELECT wc_id, group_letter, SUM(points) as total_points, COUNT(*) as teams
        FROM group_standings GROUP BY wc_id, group_letter
    """).fetchall()
    
    for s in standings:
        if s["teams"] != 4:
            results["warnings"].append(f"Group {s['group_letter']} WC{s['wc_id']} has {s['teams']} teams (expected 4)")
    
    # 5. Check referential integrity
    teams = conn.execute("SELECT wc_id, name FROM teams").fetchall()
    results["stats"]["teams_count"] = len(teams)
    
    # Check all teams in standings exist (need wc_id and team_name)
    standings_teams = conn.execute("""
        SELECT DISTINCT wc_id, team_name FROM group_standings
    """).fetchall()
    
    for st in standings_teams:
        team_exists = conn.execute(
            "SELECT 1 FROM teams WHERE wc_id=? AND name=?", 
            (st["wc_id"], st["team_name"])
        ).fetchone()
        if not team_exists:
            results["warnings"].append(f"Team {st['team_name']} in WC{st['wc_id']} not found in teams table")
    
    conn.close()
    return results


def print_validation_report(results: Dict[str, Any]):
    """Print human-readable validation report."""
    print("=" * 60)
    print("DATA QUALITY VALIDATION REPORT")
    print("=" * 60)
    
    if results["valid"]:
        print("✅ VALID: All critical checks passed")
    else:
        print("❌ INVALID: Critical errors found")
    
    print(f"\nStats:")
    for k, v in results["stats"].items():
        print(f"  {k}: {v}")
    
    if results["errors"]:
        print(f"\nErrors ({len(results['errors'])}):")
        for e in results["errors"]:
            print(f"  - {e}")
    
    if results["warnings"]:
        print(f"\nWarnings ({len(results['warnings'])}):")
        for w in results["warnings"]:
            print(f"  - {w}")


if __name__ == "__main__":
    import os
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "historical.db"
    )
    results = validate_historical_data(db_path)
    print_validation_report(results)