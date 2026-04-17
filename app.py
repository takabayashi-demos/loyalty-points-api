"""Loyalty Points API - Redemption Service."""
import threading
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB

# In-memory store (replaced by database in production)
_redemptions = []
_next_id = 1
_lock = threading.Lock()

NAME_MAX_LENGTH = 200
VALUE_MAX = 1_000_000


@app.route("/health")
def health():
    return jsonify({"status": "UP", "service": "loyalty-points-api"})


@app.route("/api/v1/redemption", methods=["GET"])
def list_redemptions():
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    with _lock:
        paginated = _redemptions[offset:offset + limit]
        total = len(_redemptions)

    return jsonify({
        "items": paginated,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@app.route("/api/v1/redemption", methods=["POST"])
def create_redemption():
    global _next_id

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    payload = request.get_json(silent=True) or {}

    errors = []

    name = payload.get("name")
    if not name or not isinstance(name, str):
        errors.append("name is required and must be a string")
    else:
        name = name.strip()
        if len(name) == 0:
            errors.append("name must not be blank")
        elif len(name) > NAME_MAX_LENGTH:
            errors.append(f"name must be {NAME_MAX_LENGTH} characters or fewer")

    value = payload.get("value")
    if value is None:
        errors.append("value is required")
    elif not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append("value must be a number")
    elif value <= 0:
        errors.append("value must be a positive number")
    elif value > VALUE_MAX:
        errors.append(f"value must not exceed {VALUE_MAX}")

    if errors:
        return jsonify({"errors": errors}), 400

    with _lock:
        redemption = {
            "id": str(_next_id),
            "name": name,
            "value": value,
        }
        _next_id += 1
        _redemptions.append(redemption)

    return jsonify(redemption), 201


@app.route("/api/v1/redemption/<redemption_id>", methods=["GET"])
def get_redemption(redemption_id):
    with _lock:
        for r in _redemptions:
            if r["id"] == redemption_id:
                return jsonify(r)
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
