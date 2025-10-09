import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# ✅ Use your actual verification token here — replace this with YOUR real one
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"

# ─────────────── Basic Test Endpoint ───────────────
@app.route("/")
def home():
    return jsonify({"message": "Dashboard API is running"}), 200

# ─────────────── eBay Verification Endpoint ───────────────
@app.route("/ebay/verify", methods=["GET"])
def verify_ebay():
    challenge_code = request.args.get("challenge_code")
    if not challenge_code:
        return "Missing challenge_code", 400

    # eBay expects your server to respond with your verification token exactly
    return VERIFICATION_TOKEN, 200

# ─────────────── Example Product Routes ───────────────
products = []
logs = []

@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products)

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    products.append(data)
    logs.append(f"Added product: {data.get('name')}")
    return jsonify({"message": "Product added"}), 201

# ─────────────── Run Locally ───────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

