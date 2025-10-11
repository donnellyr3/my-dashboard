from flask import Flask, jsonify, request
import os
import requests
from datetime import datetime

app = Flask(__name__)

# -----------------------------------
# Load eBay Credentials from Render
# -----------------------------------
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")


# -----------------------------------
# Base Routes
# -----------------------------------
@app.route('/')
def home():
    return jsonify({"message": "✅ My eBay Dashboard API is live"}), 200


@app.route('/api/ebay/status', methods=['GET'])
def ebay_status():
    """Check which credentials are currently loaded"""
    status = {
        "client_id_set": bool(EBAY_CLIENT_ID),
        "client_secret_set": bool(EBAY_CLIENT_SECRET),
        "refresh_token_set": bool(EBAY_REFRESH_TOKEN),
        "access_token_set": bool(EBAY_ACCESS_TOKEN),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    return jsonify(status), 200


# -----------------------------------
# Token Validation
# -----------------------------------
@app.route('/api/check_token', methods=['GET'])
def check_token():
    """Verify if current eBay Access Token is valid"""
    if not EBAY_ACCESS_TOKEN:
        return jsonify({"success": False, "message": "Access token missing"}), 400

    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    r = requests.get("https://api.ebay.com/commerce/identity/v1/user/", headers=headers)

    if r.status_code == 200:
        return jsonify({"success": True, "message": "Access token is valid"}), 200
    else:
        return jsonify({
            "success": False,
            "message": "Invalid or expired access token",
            "status_code": r.status_code,
            "response": r.text
        }), 401


# -----------------------------------
# Refresh Token Endpoint
# -----------------------------------
@app.route('/api/refresh_token', methods=['GET', 'POST'])
def refresh_token():
    """Refresh the eBay Access Token using the Refresh Token"""
    if not all([EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_REFRESH_TOKEN]):
        return jsonify({
            "success": False,
            "message": "Missing eBay credentials in environment variables"
        }), 400

    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory"
    }

    auth = (EBAY_CLIENT_ID, EBAY_CLIENT_SECRET)
    response = requests.post(url, headers=headers, data=data, auth=auth)

    if response.status_code == 200:
        token_data = response.json()
        new_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")

        return jsonify({
            "success": True,
            "message": "Access token refreshed successfully",
            "access_token": new_token,
            "expires_in_seconds": expires_in
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": "Failed to refresh token",
            "status_code": response.status_code,
            "response": response.text
        }), 400


# -----------------------------------
# Run the App
# -----------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

