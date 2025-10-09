import os
import hashlib
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Your eBay verification token (keep this exact one you used on eBay)
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"
ENDPOINT = "https://my-dashboard-tqtg.onrender.com/ebay/verify"

# -----------------------------------------------------------
# HOME ROUTE - handles OAuth redirect safely
# -----------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    if "code" in request.args:
        code = request.args.get("code")
        return f"✅ SUCCESS! Copy this entire URL including the code parameter and paste it into ChatGPT:\n\n{request.url}"
    return jsonify({"message": "Dashboard API is running"})


# -----------------------------------------------------------
# EBAY MARKETPLACE ACCOUNT DELETION VERIFICATION
# -----------------------------------------------------------
@app.route("/ebay/verify", methods=["GET", "POST"])
def ebay_verify():
    if request.method == "GET":
        challenge_code = request.args.get("challenge_code")
        if not challenge_code:
            return jsonify({"error": "Missing challenge_code"}), 400

        m = hashlib.sha256()
        m.update((challenge_code + VERIFICATION_TOKEN + ENDPOINT).encode("utf-8"))
        challenge_response = m.hexdigest()
        return jsonify({"challengeResponse": challenge_response})

    elif request.method == "POST":
        try:
            raw_data = request.get_data(as_text=True)
            print("📩 Raw Body:", raw_data)

            data = json.loads(raw_data)
            print("✅ eBay Notification received:", data)
        except Exception as e:
            print("❌ Error parsing eBay notification:", e)
            return jsonify({"error": str(e)}), 500

        return "", 200


# -----------------------------------------------------------
# SIMPLE ORDER TEST ENDPOINTS
# -----------------------------------------------------------
orders = []

@app.route("/api/orders", methods=["GET", "POST"])
def handle_orders():
    if request.method == "POST":
        data = request.json
        orders.append(data)
        return jsonify({"message": "Order added"}), 201
    return jsonify(orders)


# -----------------------------------------------------------
# SIMPLE PRODUCT TEST ENDPOINTS
# -----------------------------------------------------------
products = []

@app.route("/api/products", methods=["GET", "POST"])
def handle_products():
    if request.method == "POST":
        data = request.json
        products.append(data)
        return jsonify({"message": "Product added"}), 201
    return jsonify(products)


# -----------------------------------------------------------
# MAIN ENTRY POINT
# -----------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

