import os

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

# The MongoDB connection (MONGO_URI) is set up in api_server.py.
from api_server import api, db


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hotel-class-project-key")
app.json.sort_keys = False
app.register_blueprint(api, url_prefix="/api")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
users_collection = db.users


def create_demo_users():
    """Create two accounts for this class project if they do not exist yet."""
    users_collection.create_index("email", unique=True)

    demo_users = [
        ("Hotel Guest", "user@hotel.local", "User123!", "user"),
        ("Hotel Manager", "admin@hotel.local", "Admin123!", "admin"),
    ]

    for name, email, password, role in demo_users:
        users_collection.update_one(
            {"email": email},
            {"$setOnInsert": {
                "name": name,
                "email": email,
                "password_hash": generate_password_hash(password),
                "role": role,
            }},
            upsert=True,
        )


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

    user = users_collection.find_one({"email": email})

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    session["user_id"] = str(user["_id"])
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
