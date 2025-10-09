import os
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ Your actual eBay Verification Token
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"

# ✅ Your Render endpoint URL (must match exactly what you entered in eBay)
ENDPOINT_URL = "https://my-dashboard-tqtg.onrender.com/ebay/verify"

# -----------------------------
# Products (Example)
# -----------------------------
products = []

@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products)

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    products.append(data)
    return jsonify({"message": "Product added"}), 201

# -----------------------------
# Orders (Example)
# -----------------------------
orders = []

@app.route("/api/orders", methods=["GET"])
def get_orders():
    return jsonify(orders)

@app.route("/api/orders", methods=["POST"])
def add_order():
    data = request.json
    orders.append(data)
    return jsonify({"message": "Order added"}), 201

# -----------------------------
# eBay Verification (GET)
# -----------------------------
@app.route("/ebay/verify", methods=["GET"])
def ebay_verify():
    challenge_code = request.args.get("challenge_code")
    if not challenge_code:
        return jsonify({"error": "Missing challenge_code"}), 400

    # Create hash: challengeCode + verificationToken + endpoint
    m = hashlib.sha256()
    m.update(challenge_code.encode("utf-8"))
    m.update(VERIFICATION_TOKEN.encode("utf-8"))
    m.update(ENDPOINT_URL.encode("utf-8"))
    response_hash = m.hexdigest()

    return jsonify({"challengeResponse": response_hash})

# -----------------------------
# eBay Notifications (POST)
# -----------------------------
@app.route("/ebay/verify", methods=["POST"])
def ebay_notifications():
    try:
        print("📩 Incoming Headers:", dict(request.headers))
        raw_body = request.data.decode("utf-8")
        print("📩 Raw Body:", raw_body)

        data = request.get_json(force=True, silent=True)
        print("✅ Parsed Notification JSON:", data)

        # For now, just acknowledge receipt
        return "", 200

    except Exception as e:
        import traceback
        print("❌ Error handling eBay notification:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Root Route
# -----------------------------
@app.route("/")
def home():
    return jsonify({"message": "Dashboard API is running"})


if __name__ == "__main__":
    # For local testing only
    app.run(host="0.0.0.0", port=5000)

