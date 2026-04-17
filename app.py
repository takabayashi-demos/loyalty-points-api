"""Loyalty Points API - Redemption Service."""
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour", "20 per minute"],
    storage_uri="memory://",
    headers_enabled=True,
)

# In-memory store (replaced by database in production)
_redemptions = []
_next_id = 1

NAME_MAX_LENGTH = 200
VALUE_MAX = 1_000_000


@app.route("/health")
@limiter.exempt
def health():
    return jsonify({"status": "UP", "service": "loyalty-points-api"})


@app.route("/api/v1/redemption", methods=["GET"])
@limiter.limit("50 per minute")
def list_redemptions():
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    paginated = _redemptions[offset:offset + limit]

    return jsonify({
        "items": paginated,
        "total": len(_redemptions),
        "limit": limit,
        "offset": offset,
    })


@app.route("/api/v1/redemption", methods=["POST"])
@limiter.limit("10 per minute")
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

    redemption = {
        "id": str(_next_id),
        "name": name,
        "value": value,
    }
    _next_id += 1
    _redemptions.append(redemption)

    return jsonify(redemption), 201


@app.route("/api/v1/redemption/<redemption_id>", methods=["GET"])
@limiter.limit("50 per minute")
def get_redemption(redemption_id):
    for r in _redemptions:
        if r["id"] == redemption_id:
            return jsonify(r)
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
