import os
from datetime import date

from bson import ObjectId
from flask import Blueprint, jsonify, request, session
from pymongo import MongoClient
from werkzeug.exceptions import HTTPException

api = Blueprint("api", __name__)

client = MongoClient(os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017"))
db = client[os.environ.get("MONGO_DB_NAME", "hotel_reservation")]

ROOM_FIELDS = ["roomNumber", "type", "price", "capacity"]


@api.errorhandler(HTTPException)
def http_error(e):
    return error(e.description, e.code)


@api.errorhandler(Exception)
def server_error(e):
    return error("Something went wrong on the server", 500)


def error(message, status):
    return jsonify({"error": message}), status


def get_user_id():
    return session.get("user_id")


def is_admin():
    return session.get("role") == "admin"


def find_by_id(collection, item_id):
    if not ObjectId.is_valid(item_id):
        return None
    return collection.find_one({"_id": ObjectId(item_id)})


def to_json(doc):
    doc["id"] = str(doc.pop("_id"))
    if "roomId" in doc:
        doc["roomId"] = str(doc["roomId"])
    return doc


def overlap_query(check_in, check_out):
    return {"status": {"$ne": "cancelled"}, "checkIn": {"$lt": check_out}, "checkOut": {"$gt": check_in}}


def check_booking(room, check_in, check_out, guests, reservation_id=None):
    try:
        start = date.fromisoformat(check_in)
        end = date.fromisoformat(check_out)
    except (TypeError, ValueError):
        return error("checkIn and checkOut must be dates like 2026-12-01", 400)
    if end <= start:
        return error("checkOut must be after checkIn", 400)
    if start < date.today():
        return error("checkIn cannot be in the past", 400)
    if not isinstance(guests, int) or guests < 1 or guests > room["capacity"]:
        return error(f"guests must be between 1 and {room['capacity']}", 400)

    query = overlap_query(check_in, check_out)
    query["roomId"] = room["_id"]
    if reservation_id:
        query["_id"] = {"$ne": reservation_id}
    if db.reservations.find_one(query):
        return error("Room is already booked for those dates", 409)
    return None


@api.get("/rooms")
def list_rooms():
    query = {}
    if request.args.get("type"):
        query["type"] = request.args["type"]
    max_price = request.args.get("maxPrice", type=float)
    if max_price is not None:
        query["price"] = {"$lte": max_price}
    check_in = request.args.get("checkIn")
    check_out = request.args.get("checkOut")
    if check_in and check_out:
        booked = db.reservations.distinct("roomId", overlap_query(check_in, check_out))
        query["_id"] = {"$nin": booked}
    return jsonify([to_json(room) for room in db.rooms.find(query)]), 200


@api.get("/rooms/<room_id>")
def get_room(room_id):
    room = find_by_id(db.rooms, room_id)
    if not room:
        return error("Room not found", 404)
    return jsonify(to_json(room)), 200


@api.post("/rooms")
def create_room():
    if not get_user_id():
        return error("Login required", 401)
    if not is_admin():
        return error("Admin only", 403)
    data = request.get_json(silent=True) or {}
    missing = [field for field in ROOM_FIELDS if field not in data]
    if missing:
        return error(f"Missing fields: {', '.join(missing)}", 400)
    room = {field: data[field] for field in ROOM_FIELDS}
    db.rooms.insert_one(room)
    return jsonify(to_json(room)), 201


@api.put("/rooms/<room_id>")
def update_room(room_id):
    if not get_user_id():
        return error("Login required", 401)
    if not is_admin():
        return error("Admin only", 403)
    room = find_by_id(db.rooms, room_id)
    if not room:
        return error("Room not found", 404)
    data = request.get_json(silent=True) or {}
    changes = {field: data[field] for field in ROOM_FIELDS if field in data}
    if not changes:
        return error(f"Send at least one of: {', '.join(ROOM_FIELDS)}", 400)
    db.rooms.update_one({"_id": room["_id"]}, {"$set": changes})
    room.update(changes)
    return jsonify(to_json(room)), 200


@api.delete("/rooms/<room_id>")
def delete_room(room_id):
    if not get_user_id():
        return error("Login required", 401)
    if not is_admin():
        return error("Admin only", 403)
    room = find_by_id(db.rooms, room_id)
    if not room:
        return error("Room not found", 404)
    db.rooms.delete_one({"_id": room["_id"]})
    return jsonify({"message": "Room deleted"}), 200


@api.post("/reservations")
def create_reservation():
    if not get_user_id():
        return error("Login required", 401)
    data = request.get_json(silent=True) or {}
    missing = [field for field in ["roomId", "checkIn", "checkOut", "guests"] if field not in data]
    if missing:
        return error(f"Missing fields: {', '.join(missing)}", 400)
    room = find_by_id(db.rooms, data["roomId"])
    if not room:
        return error("Room not found", 404)
    problem = check_booking(room, data["checkIn"], data["checkOut"], data["guests"])
    if problem:
        return problem
    reservation = {
        "userId": get_user_id(),
        "roomId": room["_id"],
        "checkIn": data["checkIn"],
        "checkOut": data["checkOut"],
        "guests": data["guests"],
        "status": "booked",
    }
    db.reservations.insert_one(reservation)
    return jsonify(to_json(reservation)), 201


@api.get("/reservations")
def list_reservations():
    if not get_user_id():
        return error("Login required", 401)
    query = {} if is_admin() else {"userId": get_user_id()}
    return jsonify([to_json(r) for r in db.reservations.find(query)]), 200


def find_own_reservation(reservation_id):
    if not get_user_id():
        return None, error("Login required", 401)
    reservation = find_by_id(db.reservations, reservation_id)
    if not reservation:
        return None, error("Reservation not found", 404)
    if reservation["userId"] != get_user_id() and not is_admin():
        return None, error("Not your reservation", 403)
    return reservation, None


@api.get("/reservations/<reservation_id>")
def get_reservation(reservation_id):
    reservation, problem = find_own_reservation(reservation_id)
    if problem:
        return problem
    return jsonify(to_json(reservation)), 200


@api.patch("/reservations/<reservation_id>")
def update_reservation(reservation_id):
    reservation, problem = find_own_reservation(reservation_id)
    if problem:
        return problem
    data = request.get_json(silent=True) or {}
    changes = {field: data[field] for field in ["checkIn", "checkOut", "guests", "status"] if field in data}
    if not changes:
        return error("Send at least one of: checkIn, checkOut, guests, status", 400)
    if changes.get("status", "booked") not in ["booked", "cancelled"]:
        return error("status must be booked or cancelled", 400)

    updated = {**reservation, **changes}
    if updated["status"] == "booked":
        room = db.rooms.find_one({"_id": reservation["roomId"]})
        if not room:
            return error("Room not found", 404)
        problem = check_booking(room, updated["checkIn"], updated["checkOut"], updated["guests"], reservation["_id"])
        if problem:
            return problem

    db.reservations.update_one({"_id": reservation["_id"]}, {"$set": changes})
    return jsonify(to_json(updated)), 200


@api.delete("/reservations/<reservation_id>")
def delete_reservation(reservation_id):
    reservation, problem = find_own_reservation(reservation_id)
    if problem:
        return problem
    db.reservations.delete_one({"_id": reservation["_id"]})
    return jsonify({"message": "Reservation cancelled"}), 200

