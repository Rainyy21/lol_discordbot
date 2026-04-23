import sqlite3

conn = sqlite3.connect("user.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        discord_id TEXT PRIMARY KEY,
        puuid TEXT NOT NULL,
        game_name TEXT,
        tag_line TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches(
        match_id TEXT PRIMARY KEY,
        data TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()


def save_user(discord_id: str, puuid: str, game_name: str, tag_line: str):
    cursor.execute(
        """
        INSERT INTO users(discord_id,puuid,game_name,tag_line)
        VALUEs (?,?,?,?)
        ON CONFLICT(discord_id) DO UPDATE SET
         puuid = excluded.puuid,
         game_name=excluded.game_name,
         tag_line=excluded.tag_line
    """,
        (discord_id, puuid, game_name, tag_line),
    )
    conn.commit()


def get_user(discord_id: str):
    cursor.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
    return cursor.fetchone()


def save_match(match_id: str, data: str):
    cursor.execute(
        "INSERT OR REPLACE INTO matches(match_id, data) VALUES (?, ?)",
        (match_id, data),
    )
    conn.commit()


def get_match(match_id: str):
    cursor.execute("SELECT data FROM matches WHERE match_id = ?", (match_id,))
    row = cursor.fetchone()
    return row[0] if row else None
