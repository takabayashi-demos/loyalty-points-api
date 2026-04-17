"""Loyalty Points API - Redemption Service."""
import logging
from flask import Flask, jsonify, request

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB

# In-memory store (replaced by database in production)
_redemptions = []
_next_id = 1

NAME_MAX_LENGTH = 200
VALUE_MAX = 1_000_000


def validate_name(name):
    """Validate redemption name field.
    
    Returns:
        tuple: (validated_name, error_message or None)
    """
    if not name or not isinstance(name, str):
        return None, "name is required and must be a string"
    
    name = name.strip()
    if len(name) == 0:
        return None, "name must not be blank"
    elif len(name) > NAME_MAX_LENGTH:
        return None, f"name must be {NAME_MAX_LENGTH} characters or fewer"
    
    return name, None


def validate_value(value):
    """Validate redemption value field.
    
    Returns:
        tuple: (value, error_message or None)
    """
    if value is None:
        return None, "value is required"
    elif not isinstance(value, (int, float)) or isinstance(value, bool):
        return None, "value must be a number"
    elif value <= 0:
        return None, "value must be a positive number"
    elif value > VALUE_MAX:
        return None, f"value must not exceed {VALUE_MAX}"
    
    return value, None


@app.route("/health")
def health():
    return jsonify({"status": "UP", "service": "loyalty-points-api"})


@app.route("/api/v1/redemption", methods=["GET"])
def list_redemptions():
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    paginated = _redemptions[offset:offset + limit]

    logger.info(f"Listed redemptions: offset={offset}, limit={limit}, total={len(_redemptions)}")

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
        logger.warning("Invalid content type received")
        return jsonify({"error": "Content-Type must be application/json"}), 415

    payload = request.get_json(silent=True) or {}

    errors = []

    # Validate name
    name, name_error = validate_name(payload.get("name"))
    if name_error:
        errors.append(name_error)

    # Validate value
    value, value_error = validate_value(payload.get("value"))
    if value_error:
        errors.append(value_error)

    if errors:
        logger.warning(f"Validation failed: {errors}")
        return jsonify({"errors": errors}), 400

    redemption = {
        "id": str(_next_id),
        "name": name,
        "value": value,
    }
    _next_id += 1
    _redemptions.append(redemption)

    logger.info(f"Created redemption: id={redemption['id']}, name={redemption['name']}, value={redemption['value']}")

    return jsonify(redemption), 201


@app.route("/api/v1/redemption/<redemption_id>", methods=["GET"])
def get_redemption(redemption_id):
    for r in _redemptions:
        if r["id"] == redemption_id:
            logger.info(f"Retrieved redemption: id={redemption_id}")
            return jsonify(r)
    
    logger.warning(f"Redemption not found: id={redemption_id}")
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
