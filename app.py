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

# eBay credentials
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")

# Render credentials (used for environment update)
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID")  # You'll add this manually in Render dashboard
RENDER_API_KEY = os.getenv("RENDER_API_KEY")        # You'll add this manually in Render dashboard

# -----------------------------------------------------
# BASIC HEALTH CHECK
# -----------------------------------------------------
@app.route("/")
def home():
    return "✅ eBay Dropshipping API Running — Auto-refresh + Render sync enabled!"

# -----------------------------------------------------
# AUTO TOKEN REFRESH FUNCTION
# -----------------------------------------------------
def refresh_ebay_token():
    """Use refresh token to get a new access token from eBay and update Render env"""
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
        os.environ["EBAY_ACCESS_TOKEN"] = new_token
        app.logger.info("✅ Access token refreshed successfully.")
        
        # Also push the new token to Render environment
        if RENDER_API_KEY and RENDER_SERVICE_ID:
            try:
                render_url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/env-vars"
                headers = {
                    "Authorization": f"Bearer {RENDER_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = [{"key": "EBAY_ACCESS_TOKEN", "value": new_token}]
                res = requests.put(render_url, json=payload, headers=headers)
                if res.status_code in [200, 201]:
                    app.logger.info("🔁 Updated EBAY_ACCESS_TOKEN on Render.")
                else:
                    app.logger.warning(f"⚠️ Failed to update Render env: {res.text}")
            except Exception as e:
                app.logger.error(f"Render sync failed: {str(e)}")
        
        return new_token
    else:
        app.logger.error(f"❌ Token refresh failed: {response.text}")
        return None

# -----------------------------------------------------
# INVENTORY ENDPOINT (AUTO REFRESH)
# -----------------------------------------------------
@app.route("/api/ebay/inventory", methods=["GET"])
def get_inventory():
    """Fetch inventory and auto-refresh if token expired."""
    global EBAY_ACCESS_TOKEN

    headers = {"Authorization": f"Bearer {EBAY_ACCESS_TOKEN}", "Content-Type": "application/json"}
    url = "https://api.ebay.com/sell/inventory/v1/inventory_item"

    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        new_token = refresh_ebay_token()
        if new_token:
            EBAY_ACCESS_TOKEN = new_token
            headers["Authorization"] = f"Bearer {EBAY_ACCESS_TOKEN}"
            response = requests.get(url, headers=headers)
            return jsonify({
                "status": "token refreshed and synced",
                "response": response.json()
            })
        else:
            return jsonify({"error": "❌ Token refresh failed"}), 401

    return jsonify({
        "status": response.status_code,
        "response": response.json()
    })

# -----------------------------------------------------
# MANUAL REFRESH
# -----------------------------------------------------
@app.route("/api/ebay/refresh", methods=["GET"])
def manual_refresh():
    new_token = refresh_ebay_token()
    if new_token:
        return jsonify({"status": "success", "access_token": new_token[:50] + "..."}), 200
    else:
        return jsonify({"status": "failed"}), 400

# -----------------------------------------------------
# RUN SERVER
# -----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

