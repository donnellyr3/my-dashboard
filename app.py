import os
import json
import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# -----------------------------
# INITIAL SETUP
# -----------------------------
load_dotenv()

app = Flask(__name__)

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "RyanDonn-MyDashbo-PRD-3c5a9178a-2b23401c")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")

# -----------------------------------------------------
# HOME ROUTE
# -----------------------------------------------------
@app.route("/")
def home():
    return "✅ eBay Dropshipping API Running — Render Deployment Successful!"

# -----------------------------------------------------
# EBAY TOKEN REFRESH
# -----------------------------------------------------
@app.route("/api/ebay/refresh", methods=["GET"])
def refresh_ebay_token():
    """Refresh eBay OAuth token using the refresh token."""
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    response = requests.post(url, headers=headers, auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET), data=data)
    if response.status_code == 200:
        new_tokens = response.json()
        app.logger.info("✅ Token refresh successful.")
        return jsonify({"status": "success", "data": new_tokens})
    else:
        app.logger.error(f"❌ Token refresh failed: {response.text}")
        return jsonify({"status": "error", "response": response.json()}), response.status_code

# -----------------------------------------------------
# EBAY CONNECTION TEST
# -----------------------------------------------------
@app.route("/api/ebay/test")
def test_ebay_connection():
    """
    Check eBay API connection using a universal endpoint.
    """
    headers = {"Authorization": f"Bearer {EBAY_ACCESS_TOKEN}"}
    url = "https://api.ebay.com/sell/marketing/v1/ad_campaign"  # Always returns a response, even if no campaigns exist

    response = requests.get(url, headers=headers)
    try:
        return jsonify({
            "status": response.status_code,
            "response": response.json()
        })
    except Exception:
        return jsonify({
            "status": response.status_code,
            "response": response.text
        })

# -----------------------------------------------------
# BASIC DATA ROUTES (mock placeholders for AutoDS logic)
# -----------------------------------------------------
orders = []
products = []

@app.route("/api/orders", methods=["GET", "POST"])
def handle_orders():
    """Manage test orders."""
    if request.method == "POST":
        new_order = request.json
        orders.append(new_order)
        return jsonify({"status": "Order added", "data": new_order})
    return jsonify(orders)

@app.route("/api/products", methods=["GET", "POST"])
def handle_products():
    """Manage test products."""
    if request.method == "POST":
        new_product = request.json
        products.append(new_product)
        return jsonify({"status": "Product added", "data": new_product})
    return jsonify(products)

# -----------------------------------------------------
# RUN SERVER
# -----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

