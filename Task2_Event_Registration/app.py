from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "events.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                event_date TEXT NOT NULL,
                location TEXT NOT NULL,
                capacity INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(event_id, email),
                FOREIGN KEY(event_id) REFERENCES events(id)
            )
        """)

@app.route("/")
def home():
    return render_template("index.html")

@app.get("/api/events")
def get_events():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT e.id, e.title, e.description, e.event_date, e.location,
                   e.capacity, COUNT(r.id) AS registered
            FROM events e
            LEFT JOIN registrations r ON e.id = r.event_id
            GROUP BY e.id
            ORDER BY e.event_date
        """).fetchall()
    return jsonify([dict(row) for row in rows])

@app.post("/api/events")
def create_event():
    data = request.get_json(silent=True) or {}
    required = ["title", "description", "event_date", "location", "capacity"]

    if any(not str(data.get(k, "")).strip() for k in required):
        return jsonify({"error": "All fields are required."}), 400

    try:
        capacity = int(data["capacity"])
        if capacity < 1:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Capacity must be a positive number."}), 400

    with get_db() as conn:
        cur = conn.execute("""
            INSERT INTO events (title, description, event_date, location, capacity)
            VALUES (?, ?, ?, ?, ?)
        """, (data["title"].strip(), data["description"].strip(),
              data["event_date"].strip(), data["location"].strip(), capacity))
        event_id = cur.lastrowid

    return jsonify({"message": "Event created", "id": event_id}), 201

@app.post("/api/events/<int:event_id>/register")
def register(event_id):
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()

    if not name or not email:
        return jsonify({"error": "Name and email are required."}), 400

    with get_db() as conn:
        event = conn.execute(
            "SELECT capacity FROM events WHERE id=?", (event_id,)
        ).fetchone()
        if not event:
            return jsonify({"error": "Event not found."}), 404

        count = conn.execute(
            "SELECT COUNT(*) AS total FROM registrations WHERE event_id=?",
            (event_id,)
        ).fetchone()["total"]

        if count >= event["capacity"]:
            return jsonify({"error": "This event is full."}), 409

        try:
            conn.execute("""
                INSERT INTO registrations (event_id, name, email, created_at)
                VALUES (?, ?, ?, ?)
            """, (event_id, name, email, datetime.utcnow().isoformat()))
        except sqlite3.IntegrityError:
            return jsonify({"error": "This email is already registered."}), 409

    return jsonify({"message": "Registration successful"}), 201

@app.get("/api/events/<int:event_id>/registrations")
def registrations(event_id):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, name, email, created_at
            FROM registrations WHERE event_id=?
            ORDER BY id DESC
        """, (event_id,)).fetchall()
    return jsonify([dict(row) for row in rows])

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
