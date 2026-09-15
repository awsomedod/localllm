import sqlite3
conn = sqlite3.connect("congress.db")
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript("""
CREATE TABLE IF NOT EXISTS congress_members (
    bioguide_id TEXT PRIMARY KEY,
    name TEXT,
    first_name TEXT,
    last_name TEXT,
    honorific_name TEXT,
    birth_year TEXT,
    death_year TEXT,
    cosponsored_legislation_count INTEGER,
    sponsored_legislation_count INTEGER,
    party TEXT,
    chamber TEXT,
    member_type TEXT,
    congress INTEGER,
    start_year INTEGER,
    end_year INTEGER,
    state TEXT,
    state_code TEXT,
    district INTEGER,
    image_url TEXT
);

CREATE TABLE IF NOT EXISTS house_votes (
    vote_id INTEGER PRIMARY KEY,
    congress INTEGER,
    legislation_number TEXT,
    legislation_type TEXT,
    legislation_url TEXT,
    result TEXT,
    roll_call_number INTEGER,
    session_number INTEGER,
    source_data_url TEXT,
    start_date TEXT,
    update_date TEXT,
    url TEXT,
    vote_type TEXT
);

""")
conn.commit()
conn.close()