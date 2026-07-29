import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'worldcup.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def seed():
    conn = get_conn()
    c = conn.cursor()

    # ── STADIUMS ──
    stadiums = [
        ('Estadio Azteca (Mexico City Stadium)', 'Mexico City', 'Mexico', 80824, 'Central'),
        ('MetLife Stadium (New York New Jersey Stadium)', 'East Rutherford', 'USA', 80663, 'Eastern'),
        ("AT&T Stadium (Dallas Stadium)", 'Arlington', 'USA', 70649, 'Central'),
        ("SoFi Stadium (Los Angeles Stadium)", 'Inglewood', 'USA', 70492, 'Western'),
        ('Arrowhead Stadium (Kansas City Stadium)', 'Kansas City', 'USA', 69045, 'Central'),
        ("Levi's Stadium (San Francisco Bay Area Stadium)", 'Santa Clara', 'USA', 68827, 'Western'),
        ('NRG Stadium (Houston Stadium)', 'Houston', 'USA', 68777, 'Central'),
        ('Lincoln Financial Field (Philadelphia Stadium)', 'Philadelphia', 'USA', 68324, 'Eastern'),
        ('Mercedes-Benz Stadium (Atlanta Stadium)', 'Atlanta', 'USA', 68239, 'Eastern'),
        ('Lumen Field (Seattle Stadium)', 'Seattle', 'USA', 66925, 'Western'),
        ('Hard Rock Stadium (Miami Stadium)', 'Miami Gardens', 'USA', 64478, 'Eastern'),
        ('Gillette Stadium (Boston Stadium)', 'Foxborough', 'USA', 64146, 'Eastern'),
        ('BC Place (BC Place Vancouver)', 'Vancouver', 'Canada', 52497, 'Western'),
        ('Estadio BBVA (Estadio Monterrey)', 'Guadalupe', 'Mexico', 51243, 'Central'),
        ('Estadio Akron (Estadio Guadalajara)', 'Zapopan', 'Mexico', 45664, 'Central'),
        ('BMO Field (Toronto Stadium)', 'Toronto', 'Canada', 43036, 'Eastern'),
    ]
    c.executemany('INSERT INTO stadiums (name, host_city, country, capacity, region) VALUES (?,?,?,?,?)', stadiums)

    # ── TEAMS ──
    teams = [
        # AFC
        ('Australia', 'AFC', 27, 0), ('Iran', 'AFC', 20, 0), ('Iraq', 'AFC', 57, 0),
        ('Japan', 'AFC', 18, 0), ('Jordan', 'AFC', 63, 1), ('Qatar', 'AFC', 56, 0),
        ('Saudi Arabia', 'AFC', 61, 0), ('South Korea', 'AFC', 25, 0), ('Uzbekistan', 'AFC', 50, 1),
        # CAF
        ('Algeria', 'CAF', 28, 0), ('Cape Verde', 'CAF', 67, 1), ('DR Congo', 'CAF', 46, 0),
        ('Egypt', 'CAF', 29, 0), ('Ghana', 'CAF', 73, 0), ('Ivory Coast', 'CAF', 33, 0),
        ('Morocco', 'CAF', 7, 0), ('Senegal', 'CAF', 15, 0), ('South Africa', 'CAF', 60, 0),
        ('Tunisia', 'CAF', 45, 0),
        # CONCACAF
        ('Canada', 'CONCACAF', 30, 0), ('Curaçao', 'CONCACAF', 82, 1), ('Haiti', 'CONCACAF', 83, 0),
        ('Mexico', 'CONCACAF', 14, 0), ('Panama', 'CONCACAF', 34, 0), ('United States', 'CONCACAF', 17, 0),
        # CONMEBOL
        ('Argentina', 'CONMEBOL', 1, 0), ('Brazil', 'CONMEBOL', 6, 0), ('Colombia', 'CONMEBOL', 13, 0),
        ('Ecuador', 'CONMEBOL', 23, 0), ('Paraguay', 'CONMEBOL', 41, 0), ('Uruguay', 'CONMEBOL', 16, 0),
        # OFC
        ('New Zealand', 'OFC', 85, 0),
        # UEFA
        ('Austria', 'UEFA', 24, 0), ('Belgium', 'UEFA', 9, 0), ('Bosnia and Herzegovina', 'UEFA', 64, 0),
        ('Croatia', 'UEFA', 11, 0), ('Czech Republic', 'UEFA', 40, 0), ('England', 'UEFA', 4, 0),
        ('France', 'UEFA', 3, 0), ('Germany', 'UEFA', 10, 0), ('Netherlands', 'UEFA', 8, 0),
        ('Norway', 'UEFA', 31, 0), ('Portugal', 'UEFA', 5, 0), ('Scotland', 'UEFA', 42, 0),
        ('Spain', 'UEFA', 2, 0), ('Sweden', 'UEFA', 38, 0), ('Switzerland', 'UEFA', 19, 0),
        ('Turkey', 'UEFA', 22, 0),
    ]
    c.executemany('INSERT INTO teams (name, confederation, fifa_ranking, debut) VALUES (?,?,?,?)', teams)

    # Map team name -> team_id
    t_map = {}
    c.execute('SELECT team_id, name FROM teams')
    for row in c.fetchall():
        t_map[row[1]] = row[0]

    # ── GROUPS ──
    groups = [chr(ord('A')+i) for i in range(12)]
    for g in groups:
        c.execute('INSERT INTO groups (group_letter) VALUES (?)', (g,))
    g_map = {}
    c.execute('SELECT group_id, group_letter FROM groups')
    for row in c.fetchall():
        g_map[row[1]] = row[0]

    # ── GROUP STANDINGS ──
    standings = [
        # (letter, pos, team, w, d, l, gf, ga, gd, pts, qualified)
        ('A',1,'Mexico',3,0,0,6,0,6,9,1),
        ('A',2,'South Africa',1,1,1,2,3,-1,4,1),
        ('A',3,'South Korea',1,0,2,2,3,-1,3,0),
        ('A',4,'Czech Republic',0,1,2,2,6,-4,1,0),
        ('B',1,'Switzerland',2,1,0,7,3,4,7,1),
        ('B',2,'Canada',1,1,1,8,3,5,4,1),
        ('B',3,'Bosnia and Herzegovina',1,1,1,5,6,-1,4,1),
        ('B',4,'Qatar',0,1,2,2,10,-8,1,0),
        ('C',1,'Brazil',2,1,0,7,1,6,7,1),
        ('C',2,'Morocco',2,1,0,6,3,3,7,1),
        ('C',3,'Scotland',1,0,2,1,4,-3,3,0),
        ('C',4,'Haiti',0,0,3,2,8,-6,0,0),
        ('D',1,'United States',2,0,1,8,4,4,6,1),
        ('D',2,'Australia',1,1,1,2,2,0,4,1),
        ('D',3,'Paraguay',1,1,1,2,4,-2,4,1),
        ('D',4,'Turkey',1,0,2,3,5,-2,3,0),
        ('E',1,'Germany',2,0,1,10,4,6,6,1),
        ('E',2,'Ivory Coast',2,0,1,4,2,2,6,1),
        ('E',3,'Ecuador',1,1,1,2,2,0,4,1),
        ('E',4,'Curaçao',0,1,2,1,9,-8,1,0),
        ('F',1,'Netherlands',2,1,0,10,4,6,7,1),
        ('F',2,'Japan',1,2,0,7,3,4,5,1),
        ('F',3,'Sweden',1,1,1,7,7,0,4,1),
        ('F',4,'Tunisia',0,0,3,2,12,-10,0,0),
        ('G',1,'Belgium',1,2,0,6,2,4,5,1),
        ('G',2,'Egypt',1,2,0,5,3,2,5,1),
        ('G',3,'Iran',0,3,0,3,3,0,3,0),
        ('G',4,'New Zealand',0,1,2,4,10,-6,1,0),
        ('H',1,'Spain',2,1,0,5,0,5,7,1),
        ('H',2,'Cape Verde',0,3,0,2,2,0,3,1),
        ('H',3,'Uruguay',0,2,1,3,4,-1,2,0),
        ('H',4,'Saudi Arabia',0,2,1,1,5,-4,2,0),
        ('I',1,'France',3,0,0,10,2,8,9,1),
        ('I',2,'Norway',2,0,1,8,7,1,6,1),
        ('I',3,'Senegal',1,0,2,8,6,2,3,1),
        ('I',4,'Iraq',0,0,3,1,12,-11,0,0),
        ('J',1,'Argentina',3,0,0,8,1,7,9,1),
        ('J',2,'Austria',1,1,1,6,6,0,4,1),
        ('J',3,'Algeria',1,1,1,5,7,-2,4,1),
        ('J',4,'Jordan',0,0,3,3,8,-5,0,0),
        ('K',1,'Colombia',2,1,0,4,1,3,7,1),
        ('K',2,'Portugal',1,2,0,6,1,5,5,1),
        ('K',3,'DR Congo',1,1,1,4,3,1,4,1),
        ('K',4,'Uzbekistan',0,0,3,2,11,-9,0,0),
        ('L',1,'England',2,1,0,6,2,4,7,1),
        ('L',2,'Croatia',2,0,1,5,5,0,6,1),
        ('L',3,'Ghana',1,1,1,2,2,0,4,1),
        ('L',4,'Panama',0,0,3,0,4,-4,0,0),
    ]
    for (g, pos, team, w, d, l, gf, ga, gd, pts, qual) in standings:
        c.execute('''INSERT INTO group_standings
            (group_id, team_id, pos, played, wins, draws, losses, goals_for, goals_against, goal_diff, points, qualified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (g_map[g], t_map[team], pos, 3, w, d, l, gf, ga, gd, pts, qual))

    # Helper to get stadium id by name prefix
    def sid(name_part):
        for row in stadiums:
            if row[0].startswith(name_part):
                # stadiums are in order, so index+1
                return stadiums.index(row) + 1
        return None

    # ── MATCHES ──
    matches = []

    def add_match(round_name, group_letter, match_num, date, home, away, hs, as_, hp, ap, et, stage, stad, att):
        matches.append((round_name, group_letter, match_num, date, t_map[home], t_map[away], hs, as_, hp, ap, et, stage, sid(stad), att))

    # === GROUP STAGE (72 matches) ===
    # Group A
    add_match('Group Stage','A',1,'2026-06-11','Mexico','South Africa',2,0,None,None,0,1,'Estadio Azteca',80824)
    add_match('Group Stage','A',2,'2026-06-11','South Korea','Czech Republic',2,1,None,None,0,1,'Estadio Akron',45664)
    add_match('Group Stage','A',3,'2026-06-18','Czech Republic','South Africa',1,1,None,None,0,2,'Mercedes-Benz Stadium',68239)
    add_match('Group Stage','A',4,'2026-06-18','Mexico','South Korea',1,0,None,None,0,2,'Estadio Akron',45664)
    add_match('Group Stage','A',5,'2026-06-24','Czech Republic','Mexico',0,3,None,None,0,3,'Estadio Azteca',80824)
    add_match('Group Stage','A',6,'2026-06-24','South Africa','South Korea',1,0,None,None,0,3,'Estadio BBVA',51243)

    # Group B
    add_match('Group Stage','B',7,'2026-06-12','Canada','Bosnia and Herzegovina',1,1,None,None,0,1,'BMO Field',43036)
    add_match('Group Stage','B',8,'2026-06-13','Qatar','Switzerland',1,1,None,None,0,1,"Levi's Stadium",68827)
    add_match('Group Stage','B',9,'2026-06-18','Switzerland','Bosnia and Herzegovina',4,1,None,None,0,2,'SoFi Stadium',70492)
    add_match('Group Stage','B',10,'2026-06-18','Canada','Qatar',6,0,None,None,0,2,'BC Place',52497)
    add_match('Group Stage','B',11,'2026-06-24','Switzerland','Canada',2,1,None,None,0,3,'BC Place',52497)
    add_match('Group Stage','B',12,'2026-06-24','Bosnia and Herzegovina','Qatar',3,1,None,None,0,3,'Lumen Field',66925)

    # Group C
    add_match('Group Stage','C',13,'2026-06-13','Brazil','Morocco',1,1,None,None,0,1,'MetLife Stadium',80663)
    add_match('Group Stage','C',14,'2026-06-13','Haiti','Scotland',0,1,None,None,0,1,'Gillette Stadium',64146)
    add_match('Group Stage','C',15,'2026-06-19','Scotland','Morocco',0,1,None,None,0,2,'Gillette Stadium',64146)
    add_match('Group Stage','C',16,'2026-06-19','Brazil','Haiti',3,0,None,None,0,2,'Lincoln Financial Field',68324)
    add_match('Group Stage','C',17,'2026-06-24','Scotland','Brazil',0,3,None,None,0,3,'Hard Rock Stadium',64478)
    add_match('Group Stage','C',18,'2026-06-24','Morocco','Haiti',4,2,None,None,0,3,'Mercedes-Benz Stadium',68239)

    # Group D
    add_match('Group Stage','D',19,'2026-06-12','United States','Paraguay',4,1,None,None,0,1,'SoFi Stadium',70492)
    add_match('Group Stage','D',20,'2026-06-13','Australia','Turkey',2,0,None,None,0,1,'BC Place',52497)
    add_match('Group Stage','D',21,'2026-06-19','United States','Australia',2,0,None,None,0,2,'Lumen Field',66925)
    add_match('Group Stage','D',22,'2026-06-19','Turkey','Paraguay',0,1,None,None,0,2,"Levi's Stadium",68827)
    add_match('Group Stage','D',23,'2026-06-25','Turkey','United States',3,2,None,None,0,3,'SoFi Stadium',70492)
    add_match('Group Stage','D',24,'2026-06-25','Paraguay','Australia',0,0,None,None,0,3,"Levi's Stadium",68827)

    # Group E
    add_match('Group Stage','E',25,'2026-06-14','Germany','Curaçao',7,1,None,None,0,1,'NRG Stadium',68777)
    add_match('Group Stage','E',26,'2026-06-14','Ivory Coast','Ecuador',1,0,None,None,0,1,'Lincoln Financial Field',68324)
    add_match('Group Stage','E',27,'2026-06-20','Germany','Ivory Coast',2,1,None,None,0,2,'BMO Field',43036)
    add_match('Group Stage','E',28,'2026-06-20','Ecuador','Curaçao',0,0,None,None,0,2,'Arrowhead Stadium',69045)
    add_match('Group Stage','E',29,'2026-06-25','Curaçao','Ivory Coast',0,2,None,None,0,3,'Lincoln Financial Field',68324)
    add_match('Group Stage','E',30,'2026-06-25','Ecuador','Germany',2,1,None,None,0,3,'MetLife Stadium',80663)

    # Group F
    add_match('Group Stage','F',31,'2026-06-14','Netherlands','Japan',2,2,None,None,0,1,"AT&T Stadium",70649)
    add_match('Group Stage','F',32,'2026-06-14','Sweden','Tunisia',5,1,None,None,0,1,'Estadio BBVA',51243)
    add_match('Group Stage','F',33,'2026-06-20','Netherlands','Sweden',5,1,None,None,0,2,'NRG Stadium',68777)
    add_match('Group Stage','F',34,'2026-06-20','Tunisia','Japan',0,4,None,None,0,2,'Estadio BBVA',51243)
    add_match('Group Stage','F',35,'2026-06-25','Japan','Sweden',1,1,None,None,0,3,"AT&T Stadium",70649)
    add_match('Group Stage','F',36,'2026-06-25','Tunisia','Netherlands',1,3,None,None,0,3,'Arrowhead Stadium',69045)

    # Group G
    add_match('Group Stage','G',37,'2026-06-15','Belgium','Egypt',1,1,None,None,0,1,'Lumen Field',66925)
    add_match('Group Stage','G',38,'2026-06-15','Iran','New Zealand',2,2,None,None,0,1,'SoFi Stadium',70492)
    add_match('Group Stage','G',39,'2026-06-21','Belgium','Iran',0,0,None,None,0,2,'SoFi Stadium',70492)
    add_match('Group Stage','G',40,'2026-06-21','New Zealand','Egypt',1,3,None,None,0,2,'BC Place',52497)
    add_match('Group Stage','G',41,'2026-06-26','Egypt','Iran',1,1,None,None,0,3,'Lumen Field',66925)
    add_match('Group Stage','G',42,'2026-06-26','New Zealand','Belgium',1,5,None,None,0,3,'BC Place',52497)

    # Group H
    add_match('Group Stage','H',43,'2026-06-15','Spain','Cape Verde',0,0,None,None,0,1,'Mercedes-Benz Stadium',68239)
    add_match('Group Stage','H',44,'2026-06-15','Saudi Arabia','Uruguay',1,1,None,None,0,1,'Hard Rock Stadium',64478)
    add_match('Group Stage','H',45,'2026-06-21','Spain','Saudi Arabia',4,0,None,None,0,2,'Mercedes-Benz Stadium',68239)
    add_match('Group Stage','H',46,'2026-06-21','Uruguay','Cape Verde',2,2,None,None,0,2,'Hard Rock Stadium',64478)
    add_match('Group Stage','H',47,'2026-06-26','Cape Verde','Saudi Arabia',0,0,None,None,0,3,'NRG Stadium',68777)
    add_match('Group Stage','H',48,'2026-06-26','Uruguay','Spain',0,1,None,None,0,3,'Estadio Akron',45664)

    # Group I
    add_match('Group Stage','I',49,'2026-06-16','France','Senegal',3,1,None,None,0,1,'MetLife Stadium',80663)
    add_match('Group Stage','I',50,'2026-06-16','Iraq','Norway',1,4,None,None,0,1,'Gillette Stadium',64146)
    add_match('Group Stage','I',51,'2026-06-22','France','Iraq',3,0,None,None,0,2,'Lincoln Financial Field',68324)
    add_match('Group Stage','I',52,'2026-06-22','Norway','Senegal',3,2,None,None,0,2,'MetLife Stadium',80663)
    add_match('Group Stage','I',53,'2026-06-26','Norway','France',1,4,None,None,0,3,'Gillette Stadium',64146)
    add_match('Group Stage','I',54,'2026-06-26','Senegal','Iraq',5,0,None,None,0,3,'BMO Field',43036)

    # Group J
    add_match('Group Stage','J',55,'2026-06-16','Argentina','Algeria',3,0,None,None,0,1,'Arrowhead Stadium',69045)
    add_match('Group Stage','J',56,'2026-06-16','Austria','Jordan',3,1,None,None,0,1,"Levi's Stadium",68827)
    add_match('Group Stage','J',57,'2026-06-22','Argentina','Austria',2,0,None,None,0,2,"AT&T Stadium",70649)
    add_match('Group Stage','J',58,'2026-06-22','Jordan','Algeria',1,2,None,None,0,2,"Levi's Stadium",68827)
    add_match('Group Stage','J',59,'2026-06-27','Algeria','Austria',3,3,None,None,0,3,'Arrowhead Stadium',69045)
    add_match('Group Stage','J',60,'2026-06-27','Jordan','Argentina',1,3,None,None,0,3,"AT&T Stadium",70649)

    # Group K
    add_match('Group Stage','K',61,'2026-06-17','Portugal','DR Congo',1,1,None,None,0,1,'NRG Stadium',68777)
    add_match('Group Stage','K',62,'2026-06-17','Uzbekistan','Colombia',1,3,None,None,0,1,'Estadio Azteca',80824)
    add_match('Group Stage','K',63,'2026-06-23','Portugal','Uzbekistan',5,0,None,None,0,2,'NRG Stadium',68777)
    add_match('Group Stage','K',64,'2026-06-23','Colombia','DR Congo',1,0,None,None,0,2,'Estadio Akron',45664)
    add_match('Group Stage','K',65,'2026-06-27','Colombia','Portugal',0,0,None,None,0,3,'Hard Rock Stadium',64478)
    add_match('Group Stage','K',66,'2026-06-27','DR Congo','Uzbekistan',3,1,None,None,0,3,'Mercedes-Benz Stadium',68239)

    # Group L
    add_match('Group Stage','L',67,'2026-06-17','England','Croatia',4,2,None,None,0,1,"AT&T Stadium",70649)
    add_match('Group Stage','L',68,'2026-06-17','Ghana','Panama',1,0,None,None,0,1,'BMO Field',43036)
    add_match('Group Stage','L',69,'2026-06-23','England','Ghana',0,0,None,None,0,2,'Gillette Stadium',64146)
    add_match('Group Stage','L',70,'2026-06-23','Panama','Croatia',0,1,None,None,0,2,'BMO Field',43036)
    add_match('Group Stage','L',71,'2026-06-27','Panama','England',0,2,None,None,0,3,'MetLife Stadium',80663)
    add_match('Group Stage','L',72,'2026-06-27','Croatia','Ghana',2,1,None,None,0,3,'Lincoln Financial Field',68324)

    # === KNOCKOUT STAGE ===
    # Round of 32 (matches 73-88)
    add_match('Round of 32',None,73,'2026-06-28','South Africa','Canada',0,1,None,None,0,4,'SoFi Stadium',69237)
    add_match('Round of 32',None,74,'2026-06-29','Brazil','Japan',2,1,None,None,0,4,'NRG Stadium',68777)
    add_match('Round of 32',None,75,'2026-06-29','Germany','Paraguay',1,1,3,4,1,4,'Gillette Stadium',63945)
    add_match('Round of 32',None,76,'2026-06-29','Netherlands','Morocco',1,1,2,3,1,4,'Estadio BBVA',51243)
    add_match('Round of 32',None,77,'2026-06-30','Ivory Coast','Norway',1,2,None,None,0,4,"AT&T Stadium",69665)
    add_match('Round of 32',None,78,'2026-06-30','France','Sweden',3,0,None,None,0,4,'MetLife Stadium',80663)
    add_match('Round of 32',None,79,'2026-06-30','Mexico','Ecuador',2,0,None,None,0,4,'Estadio Azteca',80824)
    add_match('Round of 32',None,80,'2026-07-01','England','DR Congo',2,1,None,None,0,4,'Mercedes-Benz Stadium',68239)
    add_match('Round of 32',None,81,'2026-07-01','Belgium','Senegal',3,2,None,None,1,4,'Lumen Field',66925)
    add_match('Round of 32',None,82,'2026-07-01','United States','Bosnia and Herzegovina',2,0,None,None,0,4,"Levi's Stadium",68827)
    add_match('Round of 32',None,83,'2026-07-02','Spain','Austria',3,0,None,None,0,4,'SoFi Stadium',70492)
    add_match('Round of 32',None,84,'2026-07-02','Portugal','Croatia',2,1,None,None,0,4,'BMO Field',43036)
    add_match('Round of 32',None,85,'2026-07-02','Switzerland','Algeria',2,0,None,None,0,4,'BC Place',52497)
    add_match('Round of 32',None,86,'2026-07-03','Australia','Egypt',1,1,2,4,1,4,"AT&T Stadium",70244)
    add_match('Round of 32',None,87,'2026-07-03','Argentina','Cape Verde',3,2,None,None,1,4,'Hard Rock Stadium',64478)
    add_match('Round of 32',None,88,'2026-07-03','Colombia','Ghana',1,0,None,None,0,4,'Arrowhead Stadium',69045)

    # Round of 16 (matches 89-96)
    add_match('Round of 16',None,89,'2026-07-04','Canada','Morocco',0,3,None,None,0,5,'NRG Stadium',68777)
    add_match('Round of 16',None,90,'2026-07-04','Paraguay','France',0,1,None,None,0,5,'Lincoln Financial Field',68324)
    add_match('Round of 16',None,91,'2026-07-05','Brazil','Norway',1,2,None,None,0,5,'MetLife Stadium',80663)
    add_match('Round of 16',None,92,'2026-07-05','Mexico','England',2,3,None,None,0,5,'Estadio Azteca',80824)
    add_match('Round of 16',None,93,'2026-07-06','Portugal','Spain',0,1,None,None,0,5,"AT&T Stadium",70649)
    add_match('Round of 16',None,94,'2026-07-06','United States','Belgium',1,4,None,None,0,5,'Lumen Field',66925)
    add_match('Round of 16',None,95,'2026-07-07','Argentina','Egypt',3,2,None,None,0,5,'Mercedes-Benz Stadium',68239)
    add_match('Round of 16',None,96,'2026-07-07','Switzerland','Colombia',0,0,4,3,1,5,'BC Place',52497)

    # Quarterfinals (matches 97-100)
    add_match('Quarterfinal',None,97,'2026-07-09','France','Morocco',2,0,None,None,0,6,'Gillette Stadium',63811)
    add_match('Quarterfinal',None,98,'2026-07-10','Spain','Belgium',2,1,None,None,0,6,'SoFi Stadium',70492)
    add_match('Quarterfinal',None,99,'2026-07-11','Norway','England',1,2,None,None,1,6,'Hard Rock Stadium',64478)
    add_match('Quarterfinal',None,100,'2026-07-11','Argentina','Switzerland',3,1,None,None,1,6,'Arrowhead Stadium',69045)

    # Semifinals (matches 101-102)
    add_match('Semifinal',None,101,'2026-07-14','France','Spain',0,2,None,None,0,7,"AT&T Stadium",70176)
    add_match('Semifinal',None,102,'2026-07-15','England','Argentina',1,2,None,None,0,7,'Mercedes-Benz Stadium',68239)

    # Third Place (match 103)
    add_match('Third Place',None,103,'2026-07-18','France','England',4,6,None,None,0,8,'Hard Rock Stadium',64478)

    # Final (match 104)
    add_match('Final',None,104,'2026-07-19','Spain','Argentina',1,0,None,None,1,8,'MetLife Stadium',80663)

    c.executemany('''INSERT INTO matches
        (round, group_letter, match_number, date, home_team_id, away_team_id,
         home_score, away_score, home_penalty, away_penalty, extra_time, stage_number, stadium_id, attendance)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', matches)

    # ── GOALS ──
    goals = [
        # Group A
        (1,'Mexico','Julian Quiñones',1),(1,'Mexico','Raul Jimenez',1),
        (2,'South Korea','Hwang In-beom',1),(2,'South Korea','Oh Hyeon-gyu',1),(2,'Czech Republic','Ladislav Krejci',1),
        (3,'Czech Republic','Michal Sadilek',1),(3,'South Africa','Thapelo Maseko',1),
        (4,'Mexico','Raul Jimenez',1),
        (5,'Mexico','Alvaro Fidalgo',1),(5,'Mexico','Luis Romo',1),(5,'Mexico','Mateo Chavez',1),
        (6,'South Africa','Teboho Mokoena',1),

        # Group B
        (7,'Canada','Stephen Eustaquio',1),(7,'Bosnia and Herzegovina','Ermin Mahmic',1),
        (8,'Qatar','Hassan Al-Haydos',1),(8,'Switzerland','Breel Embolo',1),
        (9,'Switzerland','Breel Embolo',1),(9,'Switzerland','Dan Ndoye',1),(9,'Switzerland','Rubén Vargas',1),(9,'Switzerland','Granit Xhaka',1),(9,'Bosnia and Herzegovina','Jovo Lukic',1),
        (10,'Canada','Cyle Larin',2),(10,'Canada','Jonathan David',2),(10,'Canada','Promise David',1),(10,'Canada','Nathan Saliba',1),
        (11,'Switzerland','Dan Ndoye',1),(11,'Switzerland','Breel Embolo',1),(11,'Canada','Jonathan David',1),
        (12,'Bosnia and Herzegovina','Ermin Mahmic',1),(12,'Bosnia and Herzegovina','Kerim Alajbegovic',1),(12,'Bosnia and Herzegovina','Marcel Sabitzer',1),(12,'Qatar','Abdulelah Al-Amri',1),

        # Group C
        (13,'Brazil','Vinicius Junior',1),(13,'Morocco','Ismael Saibari',1),
        (14,'Scotland','John McGinn',1),
        (15,'Morocco','Ismaeil Saibari',1),
        (16,'Brazil','Matheus Cunha',1),(16,'Brazil','Vinicius Junior',1),(16,'Brazil','Casemiro',1),
        (17,'Brazil','Matheus Cunha',1),(17,'Brazil','Vinicius Junior',1),(17,'Brazil','Neymar',1),
        (18,'Morocco','Ismael Saibari',1),(18,'Morocco','Issa Diop',1),(18,'Morocco','Achraf Hakimi',1),(18,'Morocco','Gessime Yassine',1),(18,'Haiti','Kevin Pina',1),(18,'Haiti','Helio Varela',1),

        # Group D
        (19,'United States','Folarin Balogun',1),(19,'United States','Malik Tillman',1),(19,'United States','Giovanni Reyna',1),(19,'United States','Auston Trusty',1),(19,'Paraguay','Julio Enciso',1),
        (20,'Australia','Nestory Irankunda',1),(20,'Australia','Connor Metcalfe',1),
        (21,'United States','Folarin Balogun',1),(21,'United States','Alex Freeman',1),
        (22,'Paraguay','Matias Galarza',1),
        (23,'Turkey','Arda Güler',1),(23,'Turkey','Kaan Ayhan',1),(23,'Turkey','Baris Alper Yilmaz',1),(23,'United States','Sebastian Berhalter',1),(23,'United States','Folarin Balogun',1),
        (24,'Paraguay','Mauricio',1),(24,'Australia','own goal',0),

        # Group E
        (25,'Germany','Kai Havertz',2),(25,'Germany','Jamal Musiala',1),(25,'Germany','Leroy Sané',1),(25,'Germany','Felix Nmecha',1),(25,'Germany','Deniz Undav',1),(25,'Germany','Nico Schlotterbeck',1),(25,'Curaçao','Derrick Luckassen',1),
        (26,'Ivory Coast','Nicolas Pépé',1),
        (27,'Germany','Kai Havertz',1),(27,'Germany','Deniz Undav',1),(27,'Ivory Coast','Franck Kessié',1),
        (29,'Ivory Coast','Nicolas Pépé',1),(29,'Ivory Coast','Amad Diallo',1),
        (30,'Ecuador','Gonzalo Plata',1),(30,'Ecuador','Nilson Angulo',1),(30,'Germany','Kai Havertz',1),

        # Group F
        (31,'Netherlands','Cody Gakpo',1),(31,'Netherlands','Brian Brobbey',1),(31,'Japan','Daichi Kamada',1),(31,'Japan','Kaishu Sano',1),
        (32,'Sweden','Viktor Gyökeres',1),(32,'Sweden','Alexander Isak',1),(32,'Sweden','Mattias Svanberg',1),(32,'Sweden','Yasin Ayari',1),(32,'Sweden','Anthony Elanga',1),(32,'Tunisia','Hazem Mastouri',1),
        (33,'Netherlands','Brian Brobbey',1),(33,'Netherlands','Cody Gakpo',1),(33,'Netherlands','Virgil van Dijk',1),(33,'Netherlands','Jan Paul van Hecke',1),(33,'Netherlands','Crysencio Summerville',1),(33,'Sweden','Viktor Gyökeres',1),
        (34,'Japan','Ayase Ueda',2),(34,'Japan','Daizen Maeda',1),(34,'Japan','Junya Ito',1),
        (35,'Japan','Keito Nakamura',1),(35,'Sweden','Alexander Isak',1),
        (36,'Tunisia','Omar Rekik',1),(36,'Netherlands','Crysencio Summerville',1),(36,'Netherlands','Brian Brobbey',1),(36,'Netherlands','Memphis Depay',1),

        # Group G
        (37,'Belgium','Kevin De Bruyne',1),(37,'Egypt','Mohamed Salah',1),
        (38,'Iran','Mohammad Mohebi',1),(38,'Iran','Ramin Rezaeian',1),(38,'New Zealand','Elijah Just',1),(38,'New Zealand','Finn Surman',1),
        (40,'New Zealand','Elijah Just',1),(40,'Egypt','Emam Ashour',1),(40,'Egypt','Yasser Ibrahim',1),(40,'Egypt','Trézéguet',1),
        (41,'Egypt','Mostafa Ziko',1),(41,'Iran','Ramin Rezaeian',1),
        (42,'New Zealand','Elijah Just',1),(42,'Belgium','Romelu Lukaku',2),(42,'Belgium','Charles De Ketelaere',1),(42,'Belgium','Leandro Trossard',1),(42,'Belgium','Alexis Saelemaekers',1),

        # Group H
        (44,'Saudi Arabia','Abdulelah Al-Amri',1),(44,'Uruguay','Maximiliano Araujo',1),
        (45,'Spain','Mikel Oyarzabal',2),(45,'Spain','Pedro Porro',1),(45,'Spain','Álex Baena',1),
        (46,'Uruguay','Maximiliano Araujo',1),(46,'Uruguay','Agustín Canobbio',1),(46,'Cape Verde','Deroy Duarte',1),(46,'Cape Verde','Ryan Mendes',1),
        (48,'Spain','Lamine Yamal',1),

        # Group I
        (49,'France','Kylian Mbappé',2),(49,'France','Bradley Barcola',1),(49,'Senegal','Pape Gueye',1),
        (50,'Iraq','Aymen Hussein',1),(50,'Norway','Erling Haaland',2),(50,'Norway','Antonio Nusa',1),(50,'Norway','Leo Ostigard',1),
        (51,'France','Kylian Mbappé',1),(51,'France','Ousmane Dembélé',1),(51,'France','Ibrahim Mbaye',1),
        (52,'Norway','Erling Haaland',1),(52,'Norway','Andreas Schjelderup',1),(52,'Norway','Marcus Holmgren Pedersen',1),(52,'Senegal','Ismaïla Sarr',1),(52,'Senegal','Habib Diarra',1),
        (53,'Norway','Erling Haaland',1),(53,'France','Kylian Mbappé',1),(53,'France','Ousmane Dembélé',2),(53,'France','Bradley Barcola',1),
        (54,'Senegal','Ismaïla Sarr',2),(54,'Senegal','Habib Diarra',1),(54,'Senegal','Pape Gueye',1),(54,'Senegal','Iliman Ndiaye',1),

        # Group J
        (55,'Argentina','Lionel Messi',2),(55,'Argentina','Lautaro Martínez',1),
        (56,'Austria','Marko Arnautovic',2),(56,'Austria','Romano Schmid',1),(56,'Jordan','Musa Al-Taamari',1),
        (57,'Argentina','Lionel Messi',2),(57,'Argentina','Julián Alvarez',1),
        (58,'Jordan','Ali Olwan',1),(58,'Algeria','Riyad Mahrez',1),(58,'Algeria','Amine Gouiri',1),
        (59,'Algeria','Riyad Mahrez',1),(59,'Algeria','Rafik Belghali',1),(59,'Algeria','Nadhir Benbouali',1),(59,'Austria','Marko Arnautovic',1),(59,'Austria','Marcel Sabitzer',1),(59,'Austria','Romano Schmid',1),
        (60,'Jordan','Musa Al-Taamari',1),(60,'Jordan','Nizar Al-Rashdan',1),(60,'Argentina','Lionel Messi',1),(60,'Argentina','Giovani Lo Celso',1),(60,'Argentina','Lisandro Martínez',1),

        # Group K
        (61,'Portugal','Rafael Leão',1),(61,'DR Congo','Brian Cipenga',1),
        (62,'Uzbekistan','Eldor Shomurodov',1),(62,'Colombia','Jhon Arias',1),(62,'Colombia','Jaminton Campaz',1),(62,'Colombia','Luis Díaz',1),
        (63,'Portugal','Cristiano Ronaldo',2),(63,'Portugal','Gonçalo Ramos',1),(63,'Portugal','Nuno Mendes',1),(63,'Portugal','João Neves',1),
        (64,'Colombia','Daniel Muñoz',1),
        (66,'DR Congo','Brian Cipenga',1),(66,'DR Congo','Fiston Mayele',2),(66,'Uzbekistan','Abbosbek Fayzullaev',1),

        # Group L
        (67,'England','Harry Kane',2),(67,'England','Jude Bellingham',1),(67,'England','Bukayo Saka',1),(67,'Croatia','Ivan Perisic',1),(67,'Croatia','Martin Baturina',1),
        (68,'Ghana','Caleb Yirenkyi',1),
        (70,'Croatia','Petar Musa',1),
        (71,'England','Harry Kane',1),(71,'England','Jude Bellingham',1),
        (72,'Croatia','Nikola Vlasic',1),(72,'Croatia','Petar Sucic',1),(72,'Ghana','Wilson Isidor',1),

        # Round of 32
        (73,'Canada','Stephen Eustaquio',1),
        (74,'Brazil','Casemiro',1),(74,'Brazil','Gabriel Martinelli',1),(74,'Japan','Kaishu Sano',1),
        (75,'Germany','Kai Havertz',1),(75,'Paraguay','Julio Enciso',1),
        (76,'Netherlands','Cody Gakpo',1),(76,'Morocco','Issa Diop',1),
        (77,'Ivory Coast','Amad Diallo',1),(77,'Norway','Antonio Nusa',1),(77,'Norway','Erling Haaland',1),
        (78,'France','Kylian Mbappé',2),(78,'France','Bradley Barcola',1),
        (79,'Mexico','Julian Quiñones',1),(79,'Mexico','Raul Jimenez',1),
        (80,'England','Harry Kane',2),(80,'DR Congo','Brian Cipenga',1),
        (81,'Belgium','Romelu Lukaku',1),(81,'Belgium','Youri Tielemans',2),(81,'Senegal','Habib Diarra',1),(81,'Senegal','Ismaïla Sarr',1),
        (82,'United States','Folarin Balogun',1),(82,'United States','Malik Tillman',1),
        (83,'Spain','Mikel Oyarzabal',2),(83,'Spain','Pedro Porro',1),
        (84,'Portugal','Cristiano Ronaldo',1),(84,'Portugal','Gonçalo Ramos',1),(84,'Croatia','Ivan Perisic',1),
        (85,'Switzerland','Breel Embolo',1),(85,'Switzerland','Dan Ndoye',1),
        (86,'Australia','Mohamed Hany',1,'OG'),(86,'Egypt','Emam Ashour',1),(86,'Egypt','Mahmoud Saber',1),
        (87,'Argentina','Lionel Messi',1),(87,'Argentina','Lisandro Martínez',1),(87,'Argentina','Diney',1,'OG'),(87,'Cape Verde','Deroy Duarte',1),(87,'Cape Verde','Sidny Lopes Cabral',1),
        (88,'Colombia','Jhon Arias',1),

        # Round of 16
        (89,'Morocco','Azzedine Ounahi',2),(89,'Morocco','Soufiane Rahimi',1),
        (90,'France','Kylian Mbappé',1),
        (91,'Brazil','Neymar',1),(91,'Norway','Erling Haaland',2),
        (92,'Mexico','Julian Quiñones',1),(92,'Mexico','Raul Jimenez',1),(92,'England','Jude Bellingham',2),(92,'England','Harry Kane',1),
        (93,'Spain','Mikel Merino',1),
        (94,'United States','Malik Tillman',1),(94,'Belgium','Charles De Ketelaere',2),(94,'Belgium','Hans Vanaken',1),(94,'Belgium','Romelu Lukaku',1),
        (95,'Argentina','Cristian Romero',1),(95,'Argentina','Lionel Messi',1),(95,'Argentina','Enzo Fernández',1),(95,'Egypt','Yasser Ibrahim',1),(95,'Egypt','Mostafa Ziko',1),
        # Switzerland 0-0 Colombia (a.e.t., 4-3 pens) - no goals scored

        # Quarterfinals
        (97,'France','Kylian Mbappé',1),(97,'France','Ousmane Dembélé',1),
        (98,'Spain','Fabián Ruiz',1),(98,'Spain','Mikel Merino',1),(98,'Belgium','Charles De Ketelaere',1),
        (99,'Norway','Andreas Schjelderup',1),(99,'England','Jude Bellingham',2),
        (100,'Argentina','Alexis Mac Allister',1),(100,'Argentina','Lionel Messi',1),(100,'Argentina','Julián Alvarez',1),(100,'Switzerland','Dan Ndoye',1),

        # Semifinals
        (101,'Spain','Mikel Oyarzabal',1),(101,'Spain','Pedro Porro',1),
        (102,'England','Anthony Gordon',1),(102,'Argentina','Enzo Fernández',1),(102,'Argentina','Lautaro Martínez',1),

        # Third Place
        (103,'France','Kylian Mbappé',2),(103,'France','Bradley Barcola',1),(103,'France','Ousmane Dembélé',1),(103,'England','Declan Rice',1),(103,'England','Ezri Konsa',1),(103,'England','Bukayo Saka',3),(103,'England','Jude Bellingham',1),

        # Final
        (104,'Spain','Ferran Torres',1),
    ]
    goals_data = []
    for entry in goals:
        match_id, team_name, scorer, g = entry[0], entry[1], entry[2], entry[3]
        own_goal = entry[4] if len(entry) > 4 else 0
        if isinstance(own_goal, str) and own_goal == 'OG':
            own_goal = 1
        goals_data.append((match_id, t_map[team_name], scorer, g, own_goal))
    c.executemany('INSERT INTO goals (match_id, team_id, scorer, goals, own_goal) VALUES (?,?,?,?,?)', goals_data)

    # ── AWARDS ──
    awards = [
        ('Golden Ball (Best Player)', 'Rodri', t_map['Spain']),
        ('Silver Ball', 'Lionel Messi', t_map['Argentina']),
        ('Bronze Ball', 'Kylian Mbappé', t_map['France']),
        ('Golden Boot (Top Scorer)', 'Kylian Mbappé', t_map['France']),
        ('Silver Boot', 'Lionel Messi', t_map['Argentina']),
        ('Bronze Boot', 'Jude Bellingham', t_map['England']),
        ('Golden Glove (Best Goalkeeper)', 'Unai Simón', t_map['Spain']),
        ('FIFA Young Player Award', 'Pau Cubarsí', t_map['Spain']),
        ('FIFA Fair Play Trophy', 'Netherlands', t_map['Netherlands']),
    ]
    c.executemany('INSERT INTO awards (award_name, recipient, team_id) VALUES (?,?,?)', awards)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")
    print(f"Teams: {len(teams)}, Matches: {len(matches)}, Goals: {len(goals)}")

if __name__ == '__main__':
    init_db()
    seed()
