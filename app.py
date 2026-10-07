import os
from flask import Flask, jsonify, redirect, request, send_from_directory, session
from pymongo import MongoClient
from werkzeug.security import check_password_hash



app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cs485-class-demo-key")

# TODO 2 - MONGODB CONNECTION
# Import MongoClient from pymongo.
# Connect to mongodb://localhost:27017/
# Database: coffee_auth
# Collection: users
# Create users_collection.

client = MongoClient("mongodb://localhost:27017/")
db = client["coffee_auth"]
users_collection = db["users"]


@app.get("/")
def login_page():
    return send_from_directory(".", "login.html")

@app.get("/style.css")
def stylesheet():
    return send_from_directory(".", "style.css")

@app.get("/login.js")
def login_javascript():
    return send_from_directory(".", "login.js")

@app.get("/dashboard.js")
def dashboard_javascript():
    return send_from_directory(".", "dashboard.js")


# TODO 3 - POST /api/login
# Read email and password from JSON.
# Find the account in MongoDB by email.
# Make sure active is True.
# Validate with check_password_hash().
# Save user_id, name, email, role in session.
# Return name, email, role as JSON.

@app.post("/api/login")
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user = users_collection.find_one({"email": email})

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.get("active"):
        return jsonify({"error": "Account is inactive"}), 403

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = str(user["_id"])
    session["name"] = user["name"]
    session["email"] = user["email"]
    session["role"] = user["role"]

    return jsonify({
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    })


# TODO 4 - GET /api/me
# If not logged in, return 401.
# Otherwise return name, email, role.

@app.get("/api/me")
def current_user():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    return jsonify({
        "name": session["name"],
        "email": session["email"],
        "role": session["role"]
    })


# TODO 5 - GET /user
# Require login.
# Return user.html.

@app.get("/user")
def user_page():
    if "user_id" not in session:
        return redirect("/")

    return send_from_directory(".", "user.html")


# TODO 6 - GET /admin
# Require login.
# Require session role == "admin".
# Normal users must receive 403.
# Return admin.html.

@app.get("/admin")
def admin_page():
    if "user_id" not in session:
        return redirect("/")

    if session.get("role") != "admin":
        return "403 Forbidden", 403

    return send_from_directory(".", "admin.html")


# TODO 7 - POST /api/logout
# Clear the session and return JSON.

@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


if __name__ == "__main__":
    print("Open: http://localhost:5000")
    app.run(debug=True)
