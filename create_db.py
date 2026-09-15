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
    chamber TEXT NOT NULL,
    congress INTEGER NOT NULL,
    session INTEGER NOT NULL,
    roll_call INTEGER NOT NULL,
    legislation_type TEXT,
    legislation_number TEXT,
    result TEXT,
    vote_type TEXT,
    start_date TEXT,
    source_url TEXT,
    PRIMARY KEY (chamber, congress, session, roll_call)
);
CREATE TABLE IF NOT EXISTS vote_positions (
    chamber TEXT NOT NULL,
    congress INTEGER NOT NULL,
    session INTEGER NOT NULL,
    roll_call INTEGER NOT NULL,
    bioguide_id TEXT NOT NULL,
    vote_cast TEXT,
    PRIMARY KEY (chamber, congress, session, roll_call, bioguide_id)
);
""")
conn.commit()
conn.close()