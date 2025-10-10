import os
import json
import requests
import threading
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# -----------------------------------------------------
# INITIAL SETUP
# -----------------------------------------------------
load_dotenv()
app = Flask(__name__)
CORS(app)

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")

# -----------------------------------------------------
# ROOT ROUTE
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
    auth = (EBAY_CLIENT_ID, EBAY_CLIENT_SECRET)
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly"
    }

    response = requests.post(url, headers=headers, data=data, auth=auth)
    if response.status_code == 200:
        new_tokens = response.json()
        new_access = new_tokens.get("access_token")
        if new_access:
            os.environ["EBAY_ACCESS_TOKEN"] = new_access
            # Optionally, persist to .env for permanent storage
            with open(".env", "r") as f:
                lines = f.readlines()
            with open(".env", "w") as f:
                for line in lines:
                    if not line.startswith("EBAY_ACCESS_TOKEN="):
                        f.write(line)
                f.write(f"EBAY_ACCESS_TOKEN={new_access}\n")
        app.logger.info("✅ Token refresh successful.")
        return jsonify({"status": "success", "data": new_tokens})
    else:
        app.logger.error(f"❌ Token refresh failed: {response.text}")
        return jsonify({"status": "error", "response": response.json()}), response.status_code

# -----------------------------------------------------
# EBAY INVENTORY TEST
# -----------------------------------------------------
@app.route("/api/ebay/inventory", methods=["GET"])
def get_inventory():
    """Fetch active inventory items from eBay."""
    url = "https://api.ebay.com/sell/inventory/v1/inventory_item"
    headers = {"Authorization": f"Bearer {os.getenv('EBAY_ACCESS_TOKEN')}"}
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
# AUTO TOKEN REFRESH THREAD
# -----------------------------------------------------
def auto_refresh_token():
    """Background thread to refresh token every 90 minutes."""
    while True:
        try:
            print("🔄 Auto-refreshing eBay token...")
            requests.get("http://localhost:5000/api/ebay/refresh")
        except Exception as e:
            print(f"⚠️ Auto-refresh failed: {e}")
        time.sleep(5400)  # 90 minutes

threading.Thread(target=auto_refresh_token, daemon=True).start()

# -----------------------------------------------------
# RUN SERVER
# -----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

