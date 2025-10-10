kimport os
import json
import hashlib
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# -----------------------------------------------------
# INITIALIZE APP + ENV
# -----------------------------------------------------
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
load_dotenv()

# -----------------------------------------------------
# ENV VARIABLES
# -----------------------------------------------------
EBAY_CLIENT_ID = "RyanDonn-MyDashbo-PRD-3c5a9178a-2b23401c"
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")

# -----------------------------------------------------
# SIMPLE HOME PAGE
# -----------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    if "code" in request.args:
        code = request.args.get("code")
        return f"✅ SUCCESS! Copy this entire URL and paste it into ChatGPT:\n\n{request.url}"
    return jsonify({"message": "Dashboard API is running"})


# -----------------------------------------------------
# EBAY WEBHOOK VERIFICATION
# -----------------------------------------------------
@app.route("/ebay/verify", methods=["GET", "POST"])
def ebay_verify():
    if request.method == "GET":
        challenge_code = request.args.get("challenge_code")
        if not challenge_code:
            return jsonify({"error": "Missing challenge_code"}), 400

        VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"
        ENDPOINT = "https://my-dashboard-tqtg.onrender.com/ebay/verify"
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


# -----------------------------------------------------
# TOKEN REFRESH
# -----------------------------------------------------
access_token_expiry = datetime.now() + timedelta(hours=2)

def refresh_access_token():
    """Automatically refresh eBay access token"""
    global EBAY_ACCESS_TOKEN, access_token_expiry
    app.logger.info("🔄 Refreshing eBay Access Token...")
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": (
            "https://api.ebay.com/oauth/api_scope "
            "https://api.ebay.com/oauth/api_scope/sell.account "
            "https://api.ebay.com/oauth/api_scope/sell.inventory "
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
        )
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


# -----------------------------------------------------
# EBAY CONNECTION TEST
# -----------------------------------------------------
@app.route("/api/ebay/test", methods=["GET"])
def test_ebay_connection():
    """Check if eBay API + token work"""
    ensure_token_valid()
    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    url = "https://apiz.ebay.com/sell/account/v1/fulfillment-policy"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return jsonify({"status": "success", "message": "✅ eBay API connection working!"})
    else:
        return jsonify({
            "status": "error",
            "code": response.status_code,
            "response": response.text
        }), response.status_code


# -----------------------------------------------------
# BASIC DATA ROUTES
# -----------------------------------------------------
orders = []
products = []

@app.route("/api/orders", methods=["GET", "POST"])
def handle_orders():
    if request.method == "POST":
        new_order = request.json
        orders.append(new_order)
        return jsonify({"status": "Order added", "data": new_order})
    return jsonify(orders)


@app.route("/api/products", methods=["GET", "POST"])
def handle_products():
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

