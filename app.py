"""Loyalty Points API - Redemption Service."""
import logging
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory store (replaced by database in production)
_redemptions = []
_next_id = 1

NAME_MAX_LENGTH = 200
VALUE_MAX = 1_000_000


def validate_redemption_payload(payload):
    """Validate redemption payload and return errors if any.
    
    Args:
        payload: Dictionary containing redemption data
        
    Returns:
        tuple: (validated_data, errors) where validated_data is dict or None,
               and errors is list of error messages
    """
    errors = []
    validated = {}

    name = payload.get("name")
    if not name or not isinstance(name, str):
        errors.append("name is required and must be a string")
    else:
        name = name.strip()
        if len(name) == 0:
            errors.append("name must not be blank")
        elif len(name) > NAME_MAX_LENGTH:
            errors.append(f"name must be {NAME_MAX_LENGTH} characters or fewer")
        else:
            validated["name"] = name

    value = payload.get("value")
    if value is None:
        errors.append("value is required")
    elif not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append("value must be a number")
    elif value <= 0:
        errors.append("value must be a positive number")
    elif value > VALUE_MAX:
        errors.append(f"value must not exceed {VALUE_MAX}")
    else:
        validated["value"] = value

    return (validated if not errors else None, errors)


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
    
    logger.info(
        "Listed redemptions",
        extra={"limit": limit, "offset": offset, "total": len(_redemptions)}
    )

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
        logger.warning("Invalid content type", extra={"content_type": request.content_type})
        return jsonify({"error": "Content-Type must be application/json"}), 415

    payload = request.get_json(silent=True) or {}

    validated_data, errors = validate_redemption_payload(payload)

    if errors:
        logger.warning("Validation failed", extra={"errors": errors})
        return jsonify({"errors": errors}), 400

    redemption = {
        "id": str(_next_id),
        "name": validated_data["name"],
        "value": validated_data["value"],
    }
    _next_id += 1
    _redemptions.append(redemption)

    logger.info(
        "Created redemption",
        extra={"redemption_id": redemption["id"], "name": redemption["name"]}
    )

    return jsonify(redemption), 201


@app.route("/api/v1/redemption/<redemption_id>", methods=["GET"])
def get_redemption(redemption_id):
    for r in _redemptions:
        if r["id"] == redemption_id:
            logger.info("Retrieved redemption", extra={"redemption_id": redemption_id})
            return jsonify(r)
    
    logger.warning("Redemption not found", extra={"redemption_id": redemption_id})
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
