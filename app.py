import os
import sqlite3

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hotel-class-project-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get("HOTEL_DATABASE", os.path.join(BASE_DIR, "hotel.db"))


def get_database():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_demo_users():
    """Create the users table and two accounts for this class project."""
    connection = get_database()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """
    )

    demo_users = [
        ("Hotel Guest", "user@hotel.local", "User123!", "user"),
        ("Hotel Manager", "admin@hotel.local", "Admin123!", "admin"),
    ]

    for name, email, password, role in demo_users:
        connection.execute(
            """
            INSERT OR IGNORE INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, generate_password_hash(password), role),
        )

    connection.commit()
    connection.close()


# Prepare the database whenever the application starts.
create_demo_users()


@app.get("/")
def login_page():
    if session.get("user_id"):
        return redirect("/dashboard")
    return send_from_directory(BASE_DIR, "login.html")


@app.get("/login.html")
def old_login_address():
    return redirect("/")


@app.get("/dashboard")
def dashboard_page():
    if not session.get("user_id"):
        return redirect("/")
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/index.html")
def old_dashboard_address():
    return redirect("/dashboard")


@app.get("/style.css")
def stylesheet():
    return send_from_directory(BASE_DIR, "style.css")


@app.get("/login.js")
def login_javascript():
    return send_from_directory(BASE_DIR, "login.js")


@app.get("/app.js")
def dashboard_javascript():
    return send_from_directory(BASE_DIR, "app.js")


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    connection = get_database()
    user = connection.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    connection.close()

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    session["user_id"] = user["id"]
    session["name"] = user["name"]
    session["email"] = user["email"]
    session["role"] = user["role"]

    return jsonify({
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
    })


@app.get("/api/me")
def current_user():
    if not session.get("user_id"):
        return jsonify({"error": "Not logged in."}), 401

    return jsonify({
        "name": session["name"],
        "email": session["email"],
        "role": session["role"],
    })


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    print(f"Open http://localhost:{port}")
    app.run(debug=False, port=port)
