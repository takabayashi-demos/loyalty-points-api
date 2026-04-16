"""Loyalty Points API - Redemption Service."""
import os
import re
import sqlite3
from contextlib import contextmanager

from flask import Flask, g, jsonify, request

app = Flask(__name__)
DATABASE = os.environ.get("DATABASE_PATH", "loyalty.db")

MAX_NAME_LENGTH = 200
MAX_LIMIT = 100
DEFAULT_LIMIT = 20


@contextmanager
def get_db():
    """Yield a database connection with row factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS redemptions ("
            "  id TEXT PRIMARY KEY,"
            "  name TEXT NOT NULL,"
            "  value INTEGER NOT NULL,"
            "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        conn.commit()


@app.route("/health")
def health():
    return jsonify({"status": "UP", "service": "loyalty-points-api"})


@app.route("/api/v1/redemption", methods=["GET"])
def list_redemptions():
    try:
        limit = int(request.args.get("limit", DEFAULT_LIMIT))
    except (ValueError, TypeError):
        return jsonify({"error": "limit must be an integer"}), 400

    limit = max(1, min(limit, MAX_LIMIT))
    offset = request.args.get("offset", 0, type=int)
    offset = max(0, offset)

    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, value, created_at FROM redemptions "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()

    items = [{"id": r["id"], "name": r["name"], "value": r["value"]} for r in rows]
    return jsonify({"items": items, "limit": limit, "offset": offset})


@app.route("/api/v1/redemption/<redemption_id>", methods=["GET"])
def get_redemption(redemption_id):
    if not re.match(r"^[a-zA-Z0-9_-]+$", redemption_id):
        return jsonify({"error": "invalid redemption id"}), 400

    with get_db() as conn:
        row = conn.execute(
            "SELECT id, name, value, created_at FROM redemptions WHERE id = ?",
            (redemption_id,),
        ).fetchone()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify({"id": row["id"], "name": row["name"], "value": row["value"]})


@app.route("/api/v1/redemption", methods=["POST"])
def create_redemption():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "request body required"}), 400

    name = data.get("name")
    value = data.get("value")

    if not name or not isinstance(name, str):
        return jsonify({"error": "name is required and must be a string"}), 422

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return jsonify({"error": "value is required and must be a number"}), 422

    name = name.strip()
    if len(name) > MAX_NAME_LENGTH:
        return jsonify({"error": f"name must be {MAX_NAME_LENGTH} characters or fewer"}), 422

    if value < 0:
        return jsonify({"error": "value must be non-negative"}), 422

    import uuid
    redemption_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            "INSERT INTO redemptions (id, name, value) VALUES (?, ?, ?)",
            (redemption_id, name, int(value)),
        )
        conn.commit()

    return jsonify({"id": redemption_id, "name": name, "value": int(value)}), 201


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
