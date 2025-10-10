import os
import requests
import hashlib
import json
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load .env variables
load_dotenv()

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# -----------------------------
# eBay API Credentials
# -----------------------------
EBAY_CLIENT_ID = "RyanDonn-MyDashbo-PRD-3c5a9178a-2b23401c"
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")

# Track access token expiry
access_token_expiry = datetime.now() + timedelta(hours=2)

# -----------------------------
# HOME ROUTE
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    if "code" in request.args:
        code = request.args.get("code")
        return f"✅ SUCCESS! Copy this entire URL including the code parameter and paste it into ChatGPT:\n\n{request.url}"
    return jsonify({"message": "Dashboard API is running"})

# -----------------------------
# EBAY NOTIFICATION HANDLER
# -----------------------------
@app.route("/ebay/verify", methods=["GET", "POST"])
def ebay_verify():
    if request.method == "GET":
        challenge_code = request.args.get("challenge_code")
        verification_token = os.getenv("EBAY_VERIFICATION_TOKEN", "dummy-token")
        verification_response = hashlib.sha256(
            (challenge_code + verification_token + "https://my-dashboard-tqtg.onrender.com/ebay/verify").encode("utf-8")
        ).hexdigest()
        return jsonify({"challengeResponse": verification_response})

    elif request.method == "POST":
        data = request.get_json(force=True)
        app.logger.info(f"✅ eBay Notification received: {json.dumps(data, indent=2)}")
        return "", 200

# -----------------------------
# TOKEN REFRESH HANDLER
# -----------------------------
def refresh_access_token():
    global EBAY_ACCESS_TOKEN, access_token_expiry
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment"
    }
    response = requests.post(
        url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET),
        data=data
    )
    if response.status_code == 200:
        result = response.json()
        EBAY_ACCESS_TOKEN = result.get("access_token")
        access_token_expiry = datetime.now() + timedelta(seconds=result.get("expires_in", 7200))
        app.logger.info("✅ Token refreshed successfully.")
    else:
        app.logger.error(f"❌ Failed to refresh token: {response.text}")

# -----------------------------
# CHECK EBAY CONNECTION
# -----------------------------
@app.route("/api/ebay/test")
def test_ebay_connection():
    headers = {"Authorization": f"Bearer {EBAY_ACCESS_TOKEN}"}
    response = requests.get("https://api.ebay.com/sell/account/v1/fulfillment-policy", headers=headers)
    return jsonify({"status": response.status_code, "response": response.json()})

# -----------------------------
# MAIN ENTRY
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

