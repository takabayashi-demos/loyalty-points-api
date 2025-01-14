"""Loyalty Points API - Walmart Platform
Customer loyalty program and rewards.

INTENTIONAL ISSUES (for demo):
- Double-spend race condition on redemption (bug)
- Negative balance possible (bug)
- No auth on point transfer (vulnerability)
- Integer overflow on large point values (bug)
"""
from flask import Flask, request, jsonify
import os, time, random, logging, threading

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("loyalty-points-api")

members = {
    "USR-001": {"user_id": "USR-001", "name": "John Smith", "tier": "Gold", "points": 15000, "lifetime_points": 52000},
    "USR-002": {"user_id": "USR-002", "name": "Jane Doe", "tier": "Silver", "points": 8500, "lifetime_points": 24000},
    "USR-003": {"user_id": "USR-003", "name": "Bob Wilson", "tier": "Bronze", "points": 2200, "lifetime_points": 8500},
    "USR-004": {"user_id": "USR-004", "name": "Alice Chen", "tier": "Gold", "points": 22000, "lifetime_points": 78000},
}

transactions = []
tx_counter = 0

@app.route("/health")
def health():
    return jsonify({"status": "UP", "service": "loyalty-points-api", "version": "1.4.2"})

@app.route("/ready")
def ready():
    return jsonify({"status": "READY"})

@app.route("/api/v1/loyalty/<user_id>")
def get_balance(user_id):
    member = members.get(user_id)
    if not member:
        return jsonify({"error": "Member not found"}), 404
    return jsonify(member)

@app.route("/api/v1/loyalty/<user_id>/earn", methods=["POST"])
def earn_points(user_id):
    global tx_counter
    member = members.get(user_id)
    if not member:
        return jsonify({"error": "Member not found"}), 404

    data = request.get_json() or {}
    points = data.get("points", 0)
    reason = data.get("reason", "purchase")

    # ❌ BUG: No validation - can earn negative points
    member["points"] += points
    member["lifetime_points"] += points

    tx_counter += 1
    tx = {
        "tx_id": f"TX-{tx_counter:06d}",
        "user_id": user_id,
        "type": "earn",
        "points": points,
        "reason": reason,
        "balance_after": member["points"],
        "timestamp": time.time(),
    }
    transactions.append(tx)

    return jsonify(tx), 201

@app.route("/api/v1/loyalty/<user_id>/redeem", methods=["POST"])
def redeem_points(user_id):
    global tx_counter
    member = members.get(user_id)
    if not member:
        return jsonify({"error": "Member not found"}), 404

    data = request.get_json() or {}
    points = data.get("points", 0)

    # ❌ BUG: Race condition - no lock, concurrent redemptions can double-spend
    # ❌ BUG: No check for negative balance
    time.sleep(random.uniform(0.1, 0.3))  # Simulate processing
    member["points"] -= points

    tx_counter += 1
    tx = {
        "tx_id": f"TX-{tx_counter:06d}",
        "user_id": user_id,
        "type": "redeem",
        "points": -points,
        "balance_after": member["points"],
        "timestamp": time.time(),
    }
    transactions.append(tx)

    return jsonify(tx), 201

# ❌ VULNERABILITY: No authentication on point transfer
@app.route("/api/v1/loyalty/transfer", methods=["POST"])
def transfer_points():
    global tx_counter
    data = request.get_json() or {}
    from_user = data.get("from_user_id")
    to_user = data.get("to_user_id")
    points = data.get("points", 0)

    sender = members.get(from_user)
    receiver = members.get(to_user)

    if not sender or not receiver:
        return jsonify({"error": "User not found"}), 404

    # ❌ BUG: No balance check before transfer
    sender["points"] -= points
    receiver["points"] += points

    tx_counter += 1
    return jsonify({
        "tx_id": f"TX-{tx_counter:06d}",
        "from": from_user,
        "to": to_user,
        "points": points,
        "sender_balance": sender["points"],
        "receiver_balance": receiver["points"],
    }), 201

@app.route("/api/v1/loyalty/leaderboard")
def leaderboard():
    sorted_members = sorted(members.values(), key=lambda m: m["points"], reverse=True)
    return jsonify({"leaderboard": sorted_members})

@app.route("/api/v1/loyalty/transactions")
def list_transactions():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"transactions": transactions[-limit:], "total": len(transactions)})

@app.route("/metrics")
def metrics():
    total_points = sum(m["points"] for m in members.values())
    return f"""# HELP loyalty_total_points Total points across all members
# TYPE loyalty_total_points gauge
loyalty_total_points {total_points}
# HELP loyalty_members_total Total loyalty members
# TYPE loyalty_members_total gauge
loyalty_members_total {len(members)}
# HELP loyalty_transactions_total Total transactions
# TYPE loyalty_transactions_total counter
loyalty_transactions_total {tx_counter}
# HELP loyalty_service_up Service health
# TYPE loyalty_service_up gauge
loyalty_service_up 1
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
# Thread-safe redemption
# Balance floor check
# Expiration scheduler
# Transfer auth
# Partner rewards
