import os
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ Your verification token from eBay (keep this exactly the same)
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"
# ✅ Your production endpoint URL (must match eBay settings)
ENDPOINT_URL = "https://my-dashboard-tqtg.onrender.com/ebay/verify"

# ----------------------------
# ✅ HEALTH CHECK
# ----------------------------
@app.route("/")
def home():
    return jsonify({"message": "Dashboard API is running"}), 200


# ----------------------------
# ✅ PRODUCTS ENDPOINTS
# ----------------------------
products = []

@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products)

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.get_json()
    products.append(data)
    return jsonify({"message": "Product added"}), 201


# ----------------------------
# ✅ ORDERS ENDPOINTS
# ----------------------------
orders = []

@app.route("/api/orders", methods=["GET"])
def get_orders():
    return jsonify(orders)

@app.route("/api/orders", methods=["POST"])
def add_order():
    data = request.get_json()
    orders.append(data)
    return jsonify({"message": "Order added"}), 201


# ----------------------------
# ✅ eBay Marketplace Deletion Verification (GET)
# ----------------------------
@app.route("/ebay/verify", methods=["GET"])
def verify_ebay():
    """
    Respond to eBay's challenge with the correct SHA256 hash of:
    challengeCode + verificationToken + endpoint
    """
    challenge_code = request.args.get("challenge_code", "")
    if not challenge_code:
        return jsonify({"error": "Missing challenge_code"}), 400

    to_hash = challenge_code + VERIFICATION_TOKEN + ENDPOINT_URL
    response_hash = hashlib.sha256(to_hash.encode("utf-8")).hexdigest()

    return jsonify({"challengeResponse": response_hash}), 200


# ----------------------------
# ✅ eBay Marketplace Deletion Notifications (POST)
# ----------------------------
@app.route("/ebay/verify", methods=["POST"])
def ebay_notifications():
    try:
        data = request.get_json(force=True)
        print("✅ eBay Notification received:", data)
        # For now, just return 200 OK so eBay knows we accepted it
        return "", 200
    except Exception as e:
        print("❌ Error handling eBay notification:", str(e))
        return jsonify({"error": "Internal Server Error"}), 500


# ----------------------------
# ✅ START APP
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

