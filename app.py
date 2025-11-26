import os
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_file, abort, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "data.db"
VIDEO_DIR = BASE / "static" / "videos"

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET', 'change_this_secret_in_production')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = get_db()
    user = db.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    return user

@app.route("/")
def index():
    user = current_user()
    db = get_db()
    courses = db.execute("SELECT id, title, description FROM courses").fetchall()
    db.close()
    return render_template("index.html", user=user, courses=courses)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        pw_hash = generate_password_hash(password)
        db = get_db()
        try:
            db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, pw_hash))
            db.commit()
        except Exception as e:
            db.close()
            return render_template("register.html", error="Email already exists.")
        db.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,)).fetchone()
        db.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    db = get_db()
    courses = db.execute("SELECT id, title, description FROM courses").fetchall()
    p_rows = db.execute("SELECT course_id, progress_percent FROM progress WHERE user_id = ?", (user["id"],)).fetchall()
    progress = {r["course_id"]: r["progress_percent"] for r in p_rows}
    db.close()
    return render_template("dashboard.html", user=user, courses=courses, progress=progress)

@app.route("/course/<int:course_id>")
def course(course_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    db = get_db()
    course = db.execute("SELECT id, title, description, video_filename FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course:
        db.close()
        abort(404)
    quiz = db.execute("SELECT id, question, options_json, answer_index FROM quizzes WHERE course_id = ?", (course_id,)).fetchone()
    db.close()
    return render_template("course.html", user=user, course=course, quiz=quiz)

@app.route("/video/<path:filename>")
def stream_video(filename):
    # Secure path join
    file_path = VIDEO_DIR / filename
    if not file_path.exists():
        abort(404)
    range_header = request.headers.get('Range', None)
    if not range_header:
        return send_file(str(file_path), as_attachment=False)
    # Parse range header
    size = file_path.stat().st_size
    byte1, byte2 = 0, None
    m = range_header.replace('bytes=', '').split('-')
    if m[0]:
        byte1 = int(m[0])
    if len(m) > 1 and m[1]:
        byte2 = int(m[1])
    if byte2 is None:
        byte2 = size - 1
    length = byte2 - byte1 + 1
    with open(file_path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)
    rv = make_response(data)
    rv.status_code = 206
    rv.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(length))
    rv.headers.add('Content-Type', 'video/mp4')
    return rv

@app.route("/api/submit_quiz", methods=["POST"])
def submit_quiz():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthenticated"}), 401
    data = request.json
    course_id = data.get("course_id")
    selected_index = int(data.get("selected_index", -1))
    db = get_db()
    quiz = db.execute("SELECT id, answer_index FROM quizzes WHERE course_id = ?", (course_id,)).fetchone()
    if not quiz:
        db.close()
        return jsonify({"error": "quiz not found"}), 404
    correct = (selected_index == quiz["answer_index"])
    # store progress as 100% if correct, otherwise 50% (example logic)
    prog_percent = 100 if correct else 50
    # upsert progress
    cur = db.execute("SELECT id FROM progress WHERE user_id = ? AND course_id = ?", (user["id"], course_id)).fetchone()
    if cur:
        db.execute("UPDATE progress SET progress_percent = ? WHERE id = ?", (prog_percent, cur["id"]))
    else:
        db.execute("INSERT INTO progress (user_id, course_id, progress_percent) VALUES (?, ?, ?)", (user["id"], course_id, prog_percent))
    db.commit()
    db.close()
    return jsonify({"correct": correct, "progress": prog_percent})

if __name__ == '__main__':
    # ensure video dir exists
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    print("Video directory:", VIDEO_DIR)
    app.run(debug=True)
