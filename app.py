import os
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

# ----------------------------
# In-memory storage (temporary)
# ----------------------------
products = []
orders = []
logs = []

# ----------------------------
# eBay Verification Endpoint
# ----------------------------
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"  # your token
ENDPOINT_URL = "https://my-dashboard-tqtg.onrender.com/ebay/verify"  # must match exactly in eBay settings

@app.route("/ebay/verify", methods=["GET"])
def verify_ebay():
    """Handles eBay challenge verification"""
    challenge_code = request.args.get("challenge_code", "")
    if not challenge_code:
        return jsonify({"error": "Missing challenge_code"}), 400

    # Compute SHA-256 hash: challengeCode + verificationToken + endpoint
    m = hashlib.sha256()
    m.update(challenge_code.encode("utf-8"))
    m.update(VERIFICATION_TOKEN.encode("utf-8"))
    m.update(ENDPOINT_URL.encode("utf-8"))
    response_hash = m.hexdigest()

    return jsonify({"challengeResponse": response_hash}), 200


@app.route("/ebay/verify", methods=["POST"])
def receive_ebay_notifications():
    """Receives eBay push notifications (e.g., account deletion)"""
    data = request.json
    logs.append({"event": "eBay Notification", "data": data})
    return "", 200


# ----------------------------
# Products API
# ----------------------------
@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products), 200

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    products.append(data)
    logs.append({"event": "Product Added", "data": data})
    return jsonify({"message": "Product added"}), 201


# ----------------------------
# Orders API
# ----------------------------
@app.route("/api/orders", methods=["GET"])
def get_orders():
    return jsonify(orders), 200

@app.route("/api/orders", methods=["POST"])
def add_order():
    data = request.json
    orders.append(data)
    logs.append({"event": "Order Added", "data": data})
    return jsonify({"message": "Order added"}), 201


# ----------------------------
# Logs API
# ----------------------------
@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(logs), 200


# ----------------------------
# Root Route
# ----------------------------
@app.route("/")
def home():
    return jsonify({"message": "Dashboard API is running"}), 200


# ----------------------------
# Main Entry
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

