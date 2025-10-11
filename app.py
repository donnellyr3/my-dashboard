from flask import Flask, jsonify, request
import os
import requests
from datetime import datetime

app = Flask(__name__)

# -----------------------------
# eBay Credentials from .env
# -----------------------------
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")

# -----------------------------
# ROUTES
# -----------------------------
@app.route('/')
def home():
    return jsonify({"message": "✅ My eBay Dashboard API is live"}), 200

# Simple check_token route
@app.route('/api/check_token', methods=['GET'])
def check_token():
    """Verify that the current eBay access token is valid."""
    if not EBAY_ACCESS_TOKEN:
        return jsonify({"success": False, "message": "Access token missing"}), 400

    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        "https://api.ebay.com/commerce/identity/v1/user/",
        headers=headers
    )

    if response.status_code == 200:
        return jsonify({"success": True, "message": "Access token is valid"}), 200
    else:
        return jsonify({
            "success": False,
            "message": "Invalid or expired access token",
            "status_code": response.status_code,
            "response": response.text
        }), 401


# Quick system info check
@app.route('/api/ebay/status', methods=['GET'])
def ebay_status():
    status = {
        "client_id_set": bool(EBAY_CLIENT_ID),
        "client_secret_set": bool(EBAY_CLIENT_SECRET),
        "refresh_token_set": bool(EBAY_REFRESH_TOKEN),
        "access_token_set": bool(EBAY_ACCESS_TOKEN),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    return jsonify(status), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

