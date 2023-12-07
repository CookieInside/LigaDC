import requests
import sqlite3

connection = sqlite3.connect("league_bot.db")
cursor = connection.cursor()

def team_exists(team_name):
    cursor.execute('''
        SELECT * FROM teams WHERE team_name = ?
    ''', (team_name,))
    return cursor.fetchone() != None

def calculate_bet_outcomes(match_id):
    cursor.execute('''
    SELECT * FROM Bets WHERE match_id = ?
    ''', (match_id,))
    all_points = get_set_points(match_id)
    goals = get_result_type(match_id)
    result_type = goals[0] - goals[1]
    result = cursor.fetchall()
    value_points_list = []
    all_value_points = 0.0
    for i in range(len(result)):
        result[i] = list(result[i])
        player_points = 0
        if (result[i][3] - result[i][4] > 0 and result_type > 0) or (result[i][3] - result[i][4] == 0 and result_type == 0) or (result[i][3] - result[i][4] < 0 and result_type < 0):
            player_points += 1.5
            if (result[i][3] - result[i][4]) == result_type:
                player_points += 1.0
                value_points_list.append(player_points)
        all_value_points += player_points
    
    for i in range(len(result)):
        set_player_won(result[i][0], (value_points_list[i] / all_value_points) * all_points)
        set_player_points(result[i][1], get_player_points(result[i][1]) + ((value_points_list[i] / all_value_points) * all_points))
        
def get_team_name(team_id):
    cursor.execute('''
        SELECT team_name
        FROM teams
        WHERE team_id = ?
        ''',
        (team_id,)
    )
    return cursor.fetchone()[0] 
    
def get_bet_matches_info():
    update_bet_status_true()
    update_bet_status_false()
    cursor.execute('''
        SELECT team1, team2, match_date
        FROM matches
        WHERE bet_status = TRUE
    ''')
    result = cursor.fetchall()
    for i in range(len(result)):
        result[i] = list(result[i])
        result[i][0] = get_team_name(result[i][0])
        result[i][1] = get_team_name(result[i][1])
    return result

def get_current_season(league_id="bl1"):
    result = requests.get(f"https://api.openligadb.de/getavailableleagues")
    data = result.json()
    season = 0
    for i in data:
        if i["leagueShortcut"] == league_id:
            season = i["leagueSeason"]
    return season

def add_match(match_id, league_id, team1, team2, date):
    cursor.execute('''
        INSERT OR IGNORE INTO matches (match_id, league_id, team1, team2, goals1, goals2, match_date, bet_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (match_id, league_id, team1, team2, 0, 0, date, False,)
    )
    connection.commit()

def get_set_points(match_id):
    cursor.execute('''
        SELECT SUM(set_points) FROM bets WHERE match_id = ?''',
        (match_id,)
    )
    result = cursor.fetchone()
    if result:
        return int(result[0])

def get_team_id(team_name):
    cursor.execute('''
        SELECT team_id FROM teams WHERE team_name = ?               
    ''', (team_name,))
    return int(cursor.fetchone()[0])

def add_team(team_name, icon_url):
    cursor.execute('''
        INSERT OR IGNORE INTO teams (team_name, icon_link)               
        VALUES (?, ?)''',
        (team_name, icon_url,)
    )
    connection.commit()

def load_season():
    league = "bl1"
    season = get_current_season(league)
    url = f"https://api.openligadb.de/getmatchdata/{league}/{season}/"
    result = requests.get(url)
    data = result.json()
    for i in data:
        if not team_exists(i["team1"]["teamName"]):
            add_team(i["team1"]["teamName"], i["team1"]["teamIconUrl"])
        if not team_exists(i["team2"]["teamName"]):
            add_team(i["team2"]["teamName"], i["team2"]["teamIconUrl"])
        team1_id = get_team_id(i["team1"]["teamName"])
        team2_id = get_team_id(i["team2"]["teamName"])
        add_match(i["matchID"], i["leagueId"], team1_id, team2_id, i["matchDateTime"])

def update_bet_status_true():
    cursor.execute('''
        UPDATE matches SET bet_status = True WHERE match_date BETWEEN DATE("now") AND DATE("now", "+7 day")
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
    goals = [0, 0]
    if len(data["matchResults"]) > 0:
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
        calculate_bet_outcomes(i[0])

def add_player(player_tag):
    cursor.execute('''
        INSERT OR IGNORE INTO players (player_tag, points)
        VALUES (?, ?)''',
        (player_tag, 100,)
    )
    connection.commit()

def set_player_points(player_tag, new_amount):
    cursor.execute('''
        UPDATE players SET points = ?
        WHERE player_tag = ?
        ''',
        (new_amount, player_tag,)
    )
    connection.commit()

def set_player_won(bet_id, won_points):
    cursor.execute('''
        UPDATE bets SET won_points = ?
        WHERE bet_id = ?
        ''',
        (won_points, bet_id,)
    )
    connection.commit()

def get_result_type(match_id):
    cursor.execute('''
        SELECT goals1, goals2
        FROM matches
        WHERE match_id = ?
        ''',
        (match_id,)
    )
    result = cursor.fetchone()
    return(list(result))

def get_bets(match_id):
    cursor.execute('''
        SELECT player_tag, team1, team2, set_points, bet_id
        FROM bets
        WHERE match_id = ?
        ''',
        (match_id)
    )
    match_value = get_set_points(match_id)
    sum_bet_rating = 0
    result = cursor.fetchall()
    for i in range(len(result)):
        result[i] = list(result[i])

def create_bet(player_tag, match_id, team1, team2, set_points):
    if set_points <= get_player_points(player_tag):
        cursor.execute('''
            INSERT INTO bets (player_tag, match_id, team1, team2, set_points, won_points)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (player_tag, match_id, team1, team2, set_points, 0,)
        )
        set_player_points(player_tag, get_player_points(player_tag) - set_points)
        connection.commit()
        return "bet was set successfully."
    else:
        return "tried to set more points than available."

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bets (
        bet_id INTEGER PRIMARY KEY,
        player_tag TEXT,
        match_id INTEGER,
        team1 INTEGER,
        team2 INTEGER,
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
        team1 INTEGER,
        team2 INTEGER,
        goals1 INTEGER,
        goals2 INTEGER,
        match_date DATE,
        bet_status BOOLEAN
        )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        team_id INTEGER PRIMARY KEY,
        team_name TEXT,
        icon_link TEXT
    )               
''')

connection.commit()

#print(get_bet_matches_info())

#load_season()

#print(get_result_type(66634))

#add_player("testUSER")

#print(get_player_points("testUSER"))

#update_results()