import os
import hashlib
import json
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# eBay verification token and endpoint (used for marketplace account deletion)
VERIFICATION_TOKEN = os.getenv("EBAY_VERIFICATION_TOKEN", "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab")
ENDPOINT = "https://my-dashboard-tqtg.onrender.com/ebay/verify"

# eBay OAuth credentials
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "RyanDonn-MyDashbo-PRD-3c5a9178a-2b23401c")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")

# Track access token expiry
access_token_expiry = datetime.now() + timedelta(hours=2)

# -----------------------------------------------------------
# HOME ROUTE (OAuth redirect & health check)
# -----------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    if "code" in request.args:
        code = request.args.get("code")
        return f"✅ SUCCESS! Copy this entire URL including the code parameter and paste it into ChatGPT:\n\n{request.url}"
    return jsonify({"message": "Dashboard API is running"})


# -----------------------------------------------------------
# EBAY VERIFICATION ENDPOINT (MARKETPLACE ACCOUNT DELETION)
# -----------------------------------------------------------
@app.route("/ebay/verify", methods=["GET", "POST"])
def ebay_verify():
    if request.method == "GET":
        challenge_code = request.args.get("challenge_code")
        if not challenge_code:
            return jsonify({"error": "Missing challenge_code"}), 400

        # Calculate SHA-256 challenge response
        m = hashlib.sha256()
        m.update((challenge_code + VERIFICATION_TOKEN + ENDPOINT).encode("utf-8"))
        challenge_response = m.hexdigest()
        return jsonify({"challengeResponse": challenge_response})

    elif request.method == "POST":
        try:
            raw_data = request.get_data(as_text=True)
            app.logger.info(f"📩 Raw Body: {raw_data}")
            data = json.loads(raw_data)
            app.logger.info(f"✅ eBay Notification received: {data}")
        except Exception as e:
            app.logger.error(f"❌ Error parsing eBay notification: {e}")
            return jsonify({"error": str(e)}), 500
        return "", 200


# -----------------------------------------------------------
# TOKEN REFRESH HANDLER
# -----------------------------------------------------------
def refresh_access_token():
    global EBAY_ACCESS_TOKEN, access_token_expiry
    app.logger.info("Refreshing eBay Access Token...")

    url = "https://api.ebay.com/identity/v1/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope "
                 "https://api.ebay.com/oauth/api_scope/sell.inventory "
                 "https://api.ebay.com/oauth/api_scope/sell.account "
                 "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
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


# -----------------------------------------------------------
# SAMPLE ROUTES (ORDERS / PRODUCTS)
# -----------------------------------------------------------
orders = []
products = []


@app.route("/api/orders", methods=["GET", "POST"])
def handle_orders():
    if request.method == "POST":
        data = request.json
        orders.append(data)
        return jsonify({"message": "Order added successfully", "order": data})
    return jsonify(orders)


@app.route("/api/products", methods=["GET", "POST"])
def handle_products():
    if request.method == "POST":
        data = request.json
        products.append(data)
        return jsonify({"message": "Product added successfully", "product": data})
    return jsonify(products)


# -----------------------------------------------------------
# EBAY TEST ROUTE - Get Fulfillment Policies
# -----------------------------------------------------------
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


# -----------------------------------------------------------
# MAIN ENTRY POINT
# -----------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

