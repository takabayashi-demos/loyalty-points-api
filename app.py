"""Loyalty Points API - Redemption Service."""
import logging
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

import cache

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://localhost:5432/loyalty_points"
)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

MAX_BATCH_SIZE = 100


@app.route("/health")
def health():
    return jsonify({"status": "UP", "timestamp": datetime.now(timezone.utc).isoformat()})


@app.route("/api/v1/redemption", methods=["GET"])
def list_redemptions():
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))

    cache_key = f"redemptions:list:{limit}:{offset}"
    cached = cache.get_cached(cache_key)
    if cached is not None:
        return jsonify(cached)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT r.id, r.name, r.value, r.status, r.created_at,
                       rt.tier_name, rt.multiplier
                FROM redemptions r
                LEFT JOIN reward_tiers rt ON r.tier_id = rt.id
                ORDER BY r.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"limit": limit, "offset": offset},
        ).fetchall()

        count = conn.execute(
            text("SELECT count(*) FROM redemptions")
        ).scalar()

    items = [
        {
            "id": str(row[0]),
            "name": row[1],
            "value": row[2],
            "status": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "tier": {"name": row[5], "multiplier": float(row[6])} if row[5] else None,
        }
        for row in rows
    ]

    result = {"items": items, "total": count, "limit": limit, "offset": offset}
    cache.set_cached(cache_key, result, ttl=60)
    return jsonify(result)


@app.route("/api/v1/redemption/<redemption_id>", methods=["GET"])
def get_redemption(redemption_id):
    cache_key = f"redemptions:detail:{redemption_id}"
    cached = cache.get_cached(cache_key)
    if cached is not None:
        return jsonify(cached)

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT r.id, r.name, r.value, r.status, r.created_at,
                       rt.tier_name, rt.multiplier
                FROM redemptions r
                LEFT JOIN reward_tiers rt ON r.tier_id = rt.id
                WHERE r.id = :id
                """
            ),
            {"id": redemption_id},
        ).fetchone()

    if row is None:
        return jsonify({"error": "Redemption not found"}), 404

    result = {
        "id": str(row[0]),
        "name": row[1],
        "value": row[2],
        "status": row[3],
        "created_at": row[4].isoformat() if row[4] else None,
        "tier": {"name": row[5], "multiplier": float(row[6])} if row[5] else None,
    }
    cache.set_cached(cache_key, result)
    return jsonify(result)


@app.route("/api/v1/redemption", methods=["POST"])
def create_redemption():
    data = request.get_json(silent=True) or {}

    if not data.get("name") or "value" not in data:
        return jsonify({"error": "name and value are required"}), 400

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO redemptions (name, value, status, created_at)
                VALUES (:name, :value, 'pending', now())
                RETURNING id, name, value, status, created_at
                """
            ),
            {"name": data["name"], "value": data["value"]},
        ).fetchone()
        conn.commit()

    cache.invalidate("redemptions:list:*")

    return jsonify(
        {
            "id": str(row[0]),
            "name": row[1],
            "value": row[2],
            "status": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
        }
    ), 201


@app.route("/api/v1/redemption/batch", methods=["POST"])
def create_redemptions_batch():
    """Create multiple redemptions in a single request.

    Accepts a JSON body with an "items" array (max 100). Each item must
    contain "name" and "value". All rows are inserted in a single
    transaction to minimize database round-trips.
    """
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])

    if not items:
        return jsonify({"error": "items array is required"}), 400

    if len(items) > MAX_BATCH_SIZE:
        return jsonify(
            {"error": f"Batch size exceeds maximum of {MAX_BATCH_SIZE}"}
        ), 400

    errors = []
    for idx, item in enumerate(items):
        if not item.get("name") or "value" not in item:
            errors.append({"index": idx, "error": "name and value are required"})

    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    params = [{"name": item["name"], "value": item["value"]} for item in items]

    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO redemptions (name, value, status, created_at)
                VALUES (:name, :value, 'pending', now())
                RETURNING id, name, value, status, created_at
                """
            ),
            params,
        ).fetchall()
        conn.commit()

    cache.invalidate("redemptions:list:*")

    created = [
        {
            "id": str(row[0]),
            "name": row[1],
            "value": row[2],
            "status": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
        }
        for row in result
    ]

    return jsonify({"created": len(created), "items": created}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
