"""Loyalty Points API - Redemption Service."""
from flask import Flask, jsonify, request
from flask_caching import Cache

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 60

cache = Cache(app)

# In-memory store (replaced by database in production)
_redemptions = []
_redemptions_by_id = {}  # Index for O(1) lookups
_next_id = 1

NAME_MAX_LENGTH = 200
VALUE_MAX = 1_000_000


@app.route("/health")
def health():
    return jsonify({"status": "UP", "service": "loyalty-points-api"})


@app.route("/api/v1/redemption", methods=["GET"])
@cache.cached(query_string=True)
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
    _redemptions_by_id[redemption["id"]] = redemption

    cache.delete_memoized(list_redemptions)

    return jsonify(redemption), 201


@app.route("/api/v1/redemption/<redemption_id>", methods=["GET"])
def get_redemption(redemption_id):
    redemption = _redemptions_by_id.get(redemption_id)
    if redemption:
        return jsonify(redemption)
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
