"""Loyalty Points API - Redemption Service."""
from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory store (replaced by database in production)
_redemptions = []
_next_id = 1


@app.route("/health")
def health():
    return jsonify({"status": "UP", "service": "loyalty-points-api"})


@app.route("/api/v1/redemption", methods=["GET"])
def list_redemptions():
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)

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
    payload = request.get_json(silent=True) or {}

    errors = []
    if not payload.get("name"):
        errors.append("name is required")
    if "value" not in payload:
        errors.append("value is required")
    elif not isinstance(payload["value"], (int, float)) or payload["value"] <= 0:
        errors.append("value must be a positive number")

    if errors:
        return jsonify({"errors": errors}), 400

    redemption = {
        "id": str(_next_id),
        "name": payload["name"],
        "value": payload["value"],
    }
    _next_id += 1
    _redemptions.append(redemption)

    return jsonify(redemption), 201


@app.route("/api/v1/redemption/<redemption_id>", methods=["GET"])
def get_redemption(redemption_id):
    for r in _redemptions:
        if r["id"] == redemption_id:
            return jsonify(r)
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
