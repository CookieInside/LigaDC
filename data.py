import requests
import sqlite3

connection = sqlite3.connect("league_bot.db")
cursor = connection.cursor()

def get_current_season(league_id="bl1"):
    result = requests.get(f"https://api.openligadb.de/getavailableleagues")
    data = result.json()
    season = 0
    for i in data:
        if i["leagueId"] == league_id:
            season = i["leagueSeason"]
    return season

def add_match(match_id, league_id, team1, team2, date):
    cursor.execute('''
        INSERT OR IGNORE INTO matches (match_id, league_id, team1, team2, goals1, goals2, match_date, bet_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (match_id, league_id, team1, team2, 0, 0, date, False,)
    )
    connection.commit()



def load_season():
    league = "bl1"
    season = get_current_season(league)
    url = f"https://api.openligadb.de/getmatchdata/{league}/{season}"
    result = requests.get(url)
    data = result.json()
    for i in data:
        add_match(i["matchID"], i["leagueId"], i["team1"]["teamName"], i["team2"]["teamName"], i["matchDateTime"])

def update_bet_status_true():
    cursor.execute('''
        UPDATE matches SET bet_status = True WHERE match_date BETWEEN DATE("now") AND DATE("now", "+3 day")
    ''')
    connection.commit()

def update_bet_status_false():
    cursor.execute('''
        UPDATE matches SET bet_status = False WHERE match_date < DATE("now")               
    ''')
    connection.commit()
    
def get_match_result(id):
    result = requests.get(f"https://api.openligadb.de/getmatchdata/{id}/")
    data = result.json()
    goals = [None, None]
    goals[0] = int(data["matchResults"][len(data["matchResults"])-1]["pointsTeam1"])
    goals[1] = int(data["matchResults"][len(data["matchResults"])-1]["pointsTeam2"])
    return goals

def get_player_points(player_tag):
    cursor.execute('''
        SELECT points FROM players WHERE player_tag = ?''',
        (player_tag,)
    )
    result = cursor.fetchone()
    if result:
        return int(result[0])
    return -1

def add_result(match_id, goals1, goals2):
    cursor.execute('''
        UPDATE matches SET goals1 = ?, goals2 = ? WHERE match_id = ?''',
        (goals1, goals2, match_id,)
    )
    connection.commit()
    cursor.execute('''
        SELECT * FROM bets WHERE match_id = ?''',
        (match_id,)
    )
    connection.commit()

def update_results():
    cursor.execute('''
        SELECT match_id FROM matches WHERE match_date < date("now", "-2 hour");
    ''')
    result = cursor.fetchall()
    for i in result:
        goals = get_match_result(i[0])
        add_result(i[0], goals1=goals[0], goals2=goals[1])

def add_player(player_tag):
    cursor.execute('''
        INSERT OR IGNORE INTO players (player_tag, points)
        VALUES (?, ?)''',
        (player_tag, 100,)
    )
    connection.commit()

def create_bet(player_tag, match_id, team1, team2, set_points):
    if set_points <= get_player_points(player_tag):
        cursor.execute('''
            INSERT INTO bets (player_tag, match_id, team1, team2, set_points, won_points)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (player_tag, match_id, team1, team2, set_points, 0,)
        )
        connection.commit()
        return "bet was set successfully."
    else:
        return "tried to set more points than available."

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bets (
        bet_id INTEGER PRIMARY KEY,
        player_tag INTEGER,
        match_id INTEGER,
        team1 TEXT,
        team2 TEXT,
        set_points INTEGER,
        won_points INTEGER
        )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        player_tag TEXT PRIMARY KEY,
        points INTEGER
        )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY,
        league_id TEXT,
        team1 TEXT,
        team2 TEXT,
        goals1 INTEGER,
        goals2 INTEGER,
        match_date DATE,
        bet_status BOOLEAN
        )
''')
connection.commit()

load_season()

#add_player("testUSER")

#print(get_player_points("testUSER"))

#update_results()