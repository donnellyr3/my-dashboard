import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# -----------------------------------------------------
# INITIAL SETUP
# -----------------------------------------------------
load_dotenv()
app = Flask(__name__)
CORS(app)

# Load eBay credentials from environment variables
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")

# -----------------------------------------------------
# ROOT ENDPOINT
# -----------------------------------------------------
@app.route("/")
def home():
    return "✅ eBay Dropshipping API Running — Render Deployment Successful!"

# -----------------------------------------------------
# AUTO TOKEN REFRESH FUNCTION
# -----------------------------------------------------
def refresh_ebay_token():
    """Use refresh token to get a new access token from eBay"""
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    response = requests.post(url, headers=headers, data=data, auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET))

    if response.status_code == 200:
        new_token = response.json().get("access_token")
        os.environ["EBAY_ACCESS_TOKEN"] = new_token  # update memory token
        app.logger.info("✅ Access token refreshed successfully.")
        return new_token
    else:
        app.logger.error(f"❌ Token refresh failed: {response.text}")
        return None

# -----------------------------------------------------
# INVENTORY ENDPOINT (AUTO TOKEN REFRESH)
# -----------------------------------------------------
@app.route("/api/ebay/inventory", methods=["GET"])
def get_inventory():
    """Fetch eBay inventory and auto-refresh token if expired"""
    global EBAY_ACCESS_TOKEN

    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    url = "https://api.ebay.com/sell/inventory/v1/inventory_item"

    response = requests.get(url, headers=headers)

    # Auto-refresh logic
    if response.status_code == 401:
        new_token = refresh_ebay_token()
        if new_token:
            EBAY_ACCESS_TOKEN = new_token
            headers["Authorization"] = f"Bearer {EBAY_ACCESS_TOKEN}"
            response = requests.get(url, headers=headers)
            return jsonify({
                "status": "token refreshed",
                "response": response.json()
            })
        else:
            return jsonify({"error": "❌ Failed to refresh token"}), 401

    return jsonify({
        "status": response.status_code,
        "response": response.json()
    })

# -----------------------------------------------------
# REFRESH ENDPOINT (MANUAL)
# -----------------------------------------------------
@app.route("/api/ebay/refresh", methods=["GET"])
def manual_refresh():
    new_token = refresh_ebay_token()
    if new_token:
        return jsonify({"status": "success", "access_token": new_token[:50] + "..."})
    else:
        return jsonify({"status": "failed"}), 400

# -----------------------------------------------------
# RUN SERVER
# -----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

