import os
import hashlib
from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory data storage (replace with DB later)
products = []
orders = []
logs = []

# ✅ eBay Verification Token (keep this the SAME one you saved in eBay)
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"
ENDPOINT_URL = "https://my-dashboard-tqtg.onrender.com/ebay/verify"

# =============== ROUTES ===============

@app.route("/")
def home():
    return jsonify({"message": "Dashboard API is running"}), 200

# ---------- PRODUCTS ----------
@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products)

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    products.append(data)
    logs.append(f"Added product: {data.get('name')}")
    return jsonify({"message": "Product added"}), 201

# ---------- ORDERS ----------
@app.route("/api/orders", methods=["GET"])
def get_orders():
    return jsonify(orders)

@app.route("/api/orders", methods=["POST"])
def add_order():
    data = request.json
    orders.append(data)
    logs.append(f"Added order: {data.get('orderId')}")
    return jsonify({"message": "Order added"}), 201

# ---------- LOGS ----------
@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(logs)

# ---------- eBay VERIFICATION ----------
@app.route("/ebay/verify", methods=["GET"])
def ebay_verify():
    challenge_code = request.args.get("challenge_code", "")
    if not challenge_code:
        return jsonify({"error": "Missing challenge_code"}), 400

    # Hash: challengeCode + verificationToken + endpoint
    m = hashlib.sha256()
    m.update(challenge_code.encode("utf-8"))
    m.update(VERIFICATION_TOKEN.encode("utf-8"))
    m.update(ENDPOINT_URL.encode("utf-8"))
    response_hash = m.hexdigest()

    return jsonify({"challengeResponse": response_hash}), 200

@app.route("/ebay/verify", methods=["POST"])
def ebay_notifications():
    data = request.json
    # For now, just log what comes in
    logs.append(f"eBay notification received: {data}")
    print("eBay Notification:", data)
    return "", 200

# =============== RUN LOCALLY ===============
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

