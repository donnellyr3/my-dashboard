import os
import json
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# eBay OAuth credentials
EBAY_CLIENT_ID = "RyanDonn-MyDashbo-PRD-3c5a9178a-2b23401c"
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")  # store this in .env
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")

# Track token expiry
access_token_expiry = datetime.now() + timedelta(hours=2)

# In-memory mock data
orders = []
products = []


# -------------------------------------------------------
# 🔁 AUTO REFRESH EBAY TOKEN
# -------------------------------------------------------
def refresh_access_token():
    global EBAY_ACCESS_TOKEN, access_token_expiry
    app.logger.info("Refreshing eBay Access Token...")

    url = "https://api.ebay.com/identity/v1/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment"
    }

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET),
            data=data
        )
        response.raise_for_status()
        result = response.json()

        EBAY_ACCESS_TOKEN = result.get("access_token")
        access_token_expiry = datetime.now() + timedelta(seconds=result.get("expires_in", 7200))

        app.logger.info("✅ Token refreshed successfully.")
        return EBAY_ACCESS_TOKEN
    except Exception as e:
        app.logger.error(f"❌ Error refreshing token: {e}")
        return None


def ensure_token_valid():
    global access_token_expiry
    if datetime.now() >= access_token_expiry:
        refresh_access_token()


# -------------------------------------------------------
# 🧾 BASIC ROUTES
# -------------------------------------------------------
@app.route("/")
def home():
    return jsonify({"message": "Dashboard API is running"})


@app.route("/api/orders", methods=["GET", "POST"])
def handle_orders():
    if request.method == "POST":
        data = request.json
        orders.append(data)
        return jsonify({"message": "Order added"}), 201
    return jsonify(orders)


@app.route("/api/products", methods=["GET", "POST"])
def handle_products():
    if request.method == "POST":
        data = request.json
        products.append(data)
        return jsonify({"message": "Product added"}), 201
    return jsonify(products)


# -------------------------------------------------------
# 🧠 EBAY LIVE TEST — Get Fulfillment Policies
# -------------------------------------------------------
@app.route("/api/ebay/fulfillment-policies")
def get_fulfillment_policies():
    ensure_token_valid()
    url = "https://api.ebay.com/sell/account/v1/fulfillment-policy"
    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    return jsonify(response.json()), response.status_code


# -------------------------------------------------------
# 🔔 EBAY NOTIFICATION ENDPOINT
# -------------------------------------------------------
@app.route("/ebay/verify", methods=["GET", "POST"])
def verify_ebay():
    if request.method == "GET":
        challenge_code = request.args.get("challenge_code")
        verification_token = os.getenv("EBAY_VERIFICATION_TOKEN", "dummy-token")
        verification_response = f"{challenge_code}{verification_token}{verification_token}"
        return jsonify({"challengeResponse": verification_response})
    elif request.method == "POST":
        data = request.get_json(force=True)
        app.logger.info(f"✅ eBay Notification received: {json.dumps(data, indent=2)}")
        return "", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

