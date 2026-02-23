from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DATABASE = "database.db"

# -----------------------------
# CREATE DATABASE CONNECTION
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------
# CREATE USER TABLE (if not exists)
# -----------------------------
def create_tables():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

create_tables()

# -----------------------------
# HOME ROUTE
# -----------------------------
@app.route("/")
def home():
    return {"message": "Backend with database running"}

# -----------------------------
# REGISTER USER
# -----------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not name or not email or not password or not role:
        return jsonify({"error": "All fields required"}), 400

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO user (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, password, role)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400

# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
