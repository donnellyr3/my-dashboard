import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ This is your unique eBay verification token
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"

# -------------------------------
# Health Check / Root Route
# -------------------------------
@app.route("/")
def home():
    return jsonify({"message": "Dashboard API is running"}), 200

# -------------------------------
# eBay Verification Endpoint
# -------------------------------
@app.route("/ebay/verify", methods=["GET"])
def verify_ebay():
    """
    eBay will call this with a 'challenge_code' query parameter.
    You must return your verification token for eBay to approve the webhook.
    """
    challenge_code = request.args.get("challenge_code")
    if challenge_code:
        return VERIFICATION_TOKEN, 200
    return "Missing challenge_code", 400

# -------------------------------
# Example API: Products
# -------------------------------
products = []

@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products), 200

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    products.append(data)
    return jsonify({"message": "Product added"}), 201

# -------------------------------
# Run the app (for local testing)
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

