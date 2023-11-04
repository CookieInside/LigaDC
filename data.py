import requests
import sqlite3

leauge = "bl1"
saison = "2023"
url = f"https://api.openligadb.de/getmatchdata/{leauge}/{saison}"

result = requests.get(url)

data = result.json()

print(data[0])
connection = sqlite3.connect("league_bot.db")
cursor = connection.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY,
        league_ID TEXT,
        team1 INTEGER,
        team2 INTEGER,
        goals1 INTEGER,
        goals2 INTEGER
        )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        player_id INTEGER PRIMARY KEY,
        points INTEGER,
        bets INT
        )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bets (
        bet_id INTEGER PRIMARY KEY,
        player_id INTEGER,
        match_id INTEGER,
        team1 INTEGER,
        team2_INTEGER,
        set INTEGER,
        won INTEGER
        )
''')

def get_player_points(player_id):
    cursor.execute('''
        SELECT points FROM players WHERE player_id = ?''',
        (player_id,)
    )
    return int(cursor.fetchone())

def add_result(match_id, goals1, goals2):
    # add the result to the db
    cursor.execute('''
        UPDATE matches set goals1 = ?, goals2 = ? WHERE match_id = ?''',
        (goals1, goals2, match_id,)
    )
    connection.commit()
    # calculate the bets
    cursor.execute('''
        SELECT * FROM bets WHERE match_id = ?''',
        (match_id,)
    )
    connection.commit()


def create_bet(player_id, match_id, team1, team2, set):
    if set <= get_player_points(player_id):
        cursor.execute('''
            INSERT INTO bets (player_id, match_id, team1, team2, set, won)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (player_id, match_id, team1, team2, set, 0,)
        )
        connection.commit()
        return "bet was set successfully."
    else:
        return "tried to set more points than available."