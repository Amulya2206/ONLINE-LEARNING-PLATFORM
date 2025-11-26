import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

BASE = Path(__file__).resolve().parent
DB = BASE / "data.db"

conn = sqlite3.connect(DB)
c = conn.cursor()

# users
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password_hash TEXT
)
''')
# courses
c.execute('''
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    video_filename TEXT
)
''')
# quizzes
c.execute('''
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    question TEXT,
    options_json TEXT,
    answer_index INTEGER
)
''')
# progress
c.execute('''
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    course_id INTEGER,
    progress_percent INTEGER
)
''')

# sample user
pw = generate_password_hash("Password123")
try:
    c.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", ("Sample Student", "student@example.com", pw))
except Exception:
    pass

# sample course (reference a video filename: sample.mp4)
try:
    c.execute("INSERT INTO courses (title, description, video_filename) VALUES (?, ?, ?)",
              ("Intro to Flask", "A short intro lesson about Flask basics.", "sample.mp4"))
    course_id = c.lastrowid
    import json
    options = json.dumps(["Flask is a microframework", "Flask is a database", "Flask is a frontend library"])
    c.execute("INSERT INTO quizzes (course_id, question, options_json, answer_index) VALUES (?, ?, ?, ?)",
              (course_id, "What is Flask?", options, 0))
except Exception:
    pass

conn.commit()
conn.close()
print("Initialized data.db with a sample user and course. Add your sample.mp4 into static/videos/ and run app.py.")
