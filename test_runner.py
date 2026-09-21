import sys
import tempfile
import sqlite3
from pathlib import Path

# Create temp databases
tmp = Path(tempfile.mkdtemp())
hist_db = tmp / 'historical.db'
wc_db = tmp / 'worldcup.db'

# Historical DB
conn = sqlite3.connect(str(hist_db))
c = conn.cursor()
c.execute('CREATE TABLE world_cups (wc_id INTEGER PRIMARY KEY, year INTEGER, host TEXT, champion TEXT, runner_up TEXT, top_scorer TEXT, top_scorer_goals INTEGER, total_matches INTEGER, total_goals INTEGER, total_attendance INTEGER)')
c.execute('CREATE TABLE teams (id INTEGER PRIMARY KEY, wc_id INTEGER, name TEXT, confederation TEXT)')
c.execute('CREATE TABLE matches (id INTEGER PRIMARY KEY, wc_id INTEGER, round TEXT, group_letter TEXT, match_number INTEGER, date TEXT, home_team TEXT, away_team TEXT, home_score INTEGER, away_score INTEGER, home_penalty INTEGER, away_penalty INTEGER, extra_time INTEGER, attendance INTEGER)')
c.execute('CREATE TABLE goals (id INTEGER PRIMARY KEY, wc_id INTEGER, match_number INTEGER, team_name TEXT, scorer TEXT, goals INTEGER, own_goal INTEGER)')
c.execute('CREATE TABLE group_standings (id INTEGER PRIMARY KEY, wc_id INTEGER, group_letter TEXT, team_name TEXT, pos INTEGER, played INTEGER, wins INTEGER, draws INTEGER, losses INTEGER, goals_for INTEGER, goals_against INTEGER, goal_diff INTEGER, points INTEGER, qualified INTEGER)')

world_cups = [
    (1, 2014, 'Brazil', 'Germany', 'Argentina', 'James Rodriguez', 6, 64, 171, 3386819),
    (2, 2018, 'Russia', 'France', 'Croatia', 'Harry Kane', 6, 64, 169, 3031768),
    (3, 2022, 'Qatar', 'Argentina', 'France', 'Kylian Mbappe', 8, 64, 172, 3404252),
]
for wc in world_cups:
    c.execute('INSERT INTO world_cups VALUES (?,?,?,?,?,?,?,?,?,?)', wc)

teams_data = [
    (1, 'Germany', 'UEFA'), (1, 'Argentina', 'CONMEBOL'), (1, 'Netherlands', 'UEFA'),
    (1, 'Brazil', 'CONMEBOL'), (1, 'France', 'UEFA'), (1, 'Belgium', 'UEFA'),
    (2, 'France', 'UEFA'), (2, 'Croatia', 'UEFA'), (2, 'Belgium', 'UEFA'),
    (2, 'England', 'UEFA'), (2, 'Argentina', 'CONMEBOL'), (2, 'Brazil', 'CONMEBOL'),
    (3, 'Argentina', 'CONMEBOL'), (3, 'France', 'UEFA'), (3, 'Croatia', 'UEFA'),
    (3, 'Morocco', 'CAF'), (3, 'Brazil', 'CONMEBOL'), (3, 'Netherlands', 'UEFA'),
]
for wc_id, name, conf in teams_data:
    c.execute('INSERT INTO teams (wc_id, name, confederation) VALUES (?,?,?)', (wc_id, name, conf))

matches_data = [
    (1, 'Final', None, 64, '2014-07-13', 'Germany', 'Argentina', 1, 0, None, None, 1, 74738),
    (2, 'Final', None, 64, '2018-07-15', 'France', 'Croatia', 4, 2, None, None, 0, 78011),
    (3, 'Final', None, 64, '2022-12-18', 'Argentina', 'France', 3, 3, 2, 4, 1, 88966),
]
for m in matches_data:
    c.execute('INSERT INTO matches (wc_id, round, group_letter, match_number, date, home_team, away_team, home_score, away_score, home_penalty, away_penalty, extra_time, attendance) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', m)

goals_data = [(64, 'Germany', 'Thomas Muller', 5), (64, 'France', 'Kylian Mbappe', 8)]
for mn, team, scorer, goals in goals_data:
    c.execute('INSERT INTO goals (wc_id, match_number, team_name, scorer, goals) VALUES (?,?,?,?,?)', (3, mn, team, scorer, goals))

conn.commit()
conn.close()

# Worldcup DB
conn = sqlite3.connect(str(wc_db))
c = conn.cursor()
c.execute('CREATE TABLE teams (team_id INTEGER PRIMARY KEY, name TEXT, confederation TEXT, fifa_ranking INTEGER, debut INTEGER)')
wc_teams = [('Argentina', 'CONMEBOL', 1, 0), ('France', 'UEFA', 2, 0), ('Brazil', 'CONMEBOL', 3, 0)]
for name, conf, rank, debut in wc_teams:
    c.execute('INSERT INTO teams (name, confederation, fifa_ranking, debut) VALUES (?,?,?,?)', (name, conf, rank, debut))
conn.commit()
conn.close()

# Now test
import sys
sys.path.insert(0, 'src')

import match_predictor as mp
mp.HIST_DB = Path(hist_db)
mp.WC_DB = Path(wc_db)

from match_predictor import load_training_data, train_model, predict_match, get_all_teams
from data_quality import validate_historical_data

# Test data quality
results = validate_historical_data(str(hist_db))
print('Data quality: valid=' + str(results['valid']) + ', errors=' + str(len(results['errors'])) + ', warnings=' + str(len(results['warnings'])))

# Test match predictor
df, team_conf, team_rank = load_training_data()
print('Training data: ' + str(len(df)) + ' matches, labels: ' + str(df['label'].value_counts().to_dict()))

model, features, le_home, le_away, team_conf2, team_rank2 = train_model(cv_folds=3)
print('Model trained, features: ' + str(features))

result = predict_match('Argentina', 'France')
print('Prediction: ' + str(result['probabilities']))

teams = get_all_teams()
print('Teams: ' + str(len(teams)) + ' teams, first: ' + str(teams[0]))

print('All tests passed!')