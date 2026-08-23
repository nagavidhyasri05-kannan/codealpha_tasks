from flask import Flask, request, jsonify, redirect, render_template
import sqlite3
import secrets
import string
from urllib.parse import urlparse

app = Flask(__name__)
DB = "urls.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_code TEXT UNIQUE NOT NULL,
                clicks INTEGER DEFAULT 0
            )
        """)

def make_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(secrets.choice(chars) for _ in range(length))
        with get_db() as conn:
            if not conn.execute("SELECT 1 FROM urls WHERE short_code=?", (code,)).fetchone():
                return code

def valid_url(value):
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

@app.route("/")
def home():
    return render_template("index.html")

@app.post("/api/shorten")
def shorten():
    data = request.get_json(silent=True) or {}
    original_url = str(data.get("url", "")).strip()

    if not valid_url(original_url):
        return jsonify({"error": "Please enter a valid http/https URL."}), 400

    with get_db() as conn:
        existing = conn.execute(
            "SELECT short_code FROM urls WHERE original_url=?", (original_url,)
        ).fetchone()

        if existing:
            code = existing["short_code"]
        else:
            code = make_code()
            conn.execute(
                "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
                (original_url, code)
            )

    return jsonify({
        "original_url": original_url,
        "short_code": code,
        "short_url": request.host_url.rstrip("/") + "/" + code
    })

@app.get("/<code>")
def redirect_url(code):
    with get_db() as conn:
        row = conn.execute(
            "SELECT original_url FROM urls WHERE short_code=?", (code,)
        ).fetchone()
        if not row:
            return "Short URL not found", 404

        conn.execute("UPDATE urls SET clicks = clicks + 1 WHERE short_code=?", (code,))

    return redirect(row["original_url"])

@app.get("/api/urls")
def list_urls():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT original_url, short_code, clicks FROM urls ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
