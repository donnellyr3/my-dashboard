kimport os
import json
import requests
import time
import threading
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# --------------------------------------------------
# 🔧 LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------
load_dotenv()

app = Flask(__name__)
CORS(app)

# Environment
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")
EBAY_ENVIRONMENT = os.getenv("EBAY_ENVIRONMENT", "PRODUCTION")

# --------------------------------------------------
# 🏠 ROOT ENDPOINT
# --------------------------------------------------
@app.route("/")
def home():
    return jsonify({"response": "✅ eBay Dropshipping API Running — Auto Price/Stock Monitor Ready!"})

# --------------------------------------------------
# 🔄 REFRESH TOKEN
# --------------------------------------------------
def refresh_access_token():
    """Refreshes the short-term access token using the refresh token"""
    global EBAY_ACCESS_TOKEN

    print("♻️ Refreshing eBay Access Token...")
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly"
    }

    try:
        r = requests.post(url, headers=headers, auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET), data=data)
        if r.status_code == 200:
            EBAY_ACCESS_TOKEN = r.json().get("access_token")
            os.environ["EBAY_ACCESS_TOKEN"] = EBAY_ACCESS_TOKEN
            print("✅ Access token refreshed successfully.")
            return EBAY_ACCESS_TOKEN
        else:
            print("❌ Token refresh failed:", r.text)
            return None
    except Exception as e:
        print("❌ Exception during token refresh:", e)
        return None

# --------------------------------------------------
# 🔁 AUTO TOKEN REFRESH EVERY 2 HOURS
# --------------------------------------------------
def auto_refresh_loop():
    while True:
        refresh_access_token()
        time.sleep(7200)  # every 2 hours

threading.Thread(target=auto_refresh_loop, daemon=True).start()

# --------------------------------------------------
# 🧱 EBAY INVENTORY ENDPOINT
# --------------------------------------------------
@app.route("/api/ebay/inventory", methods=["GET"])
def get_inventory():
    """Fetch eBay inventory items"""
    global EBAY_ACCESS_TOKEN

    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    url = "https://api.ebay.com/sell/inventory/v1/inventory_item"
    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        # Token likely expired — refresh and retry once
        refresh_access_token()
        headers["Authorization"] = f"Bearer {EBAY_ACCESS_TOKEN}"
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({
            "error": "❌ Failed to fetch inventory",
            "status": response.status_code,
            "response": response.text
        }), response.status_code

    data = response.json()
    listings = []
    for item in data.get("inventoryItems", []):
        listings.append({
            "image": item.get("product", {}).get("imageUrls", ["https://via.placeholder.com/60"])[0],
            "title": item.get("product", {}).get("title", "Unknown Item"),
            "price": item.get("price", {}).get("value", "0.00"),
            "stock": item.get("availability", {}).get("shipToLocationAvailability", {}).get("quantity", 0),
            "status": "Active" if item.get("availability", {}).get("shipToLocationAvailability", {}).get("quantity", 0) > 0 else "Out of Stock"
        })

    return jsonify(listings)

# --------------------------------------------------
# 📦 ORDERS ENDPOINT
# --------------------------------------------------
@app.route("/api/ebay/orders", methods=["GET"])
def get_orders():
    """Fetch eBay orders from Fulfillment API"""
    global EBAY_ACCESS_TOKEN

    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    url = "https://api.ebay.com/sell/fulfillment/v1/order"
    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        refresh_access_token()
        headers["Authorization"] = f"Bearer {EBAY_ACCESS_TOKEN}"
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({
            "error": "❌ Failed to fetch orders",
            "status": response.status_code,
            "response": response.text
        }), response.status_code

    data = response.json()
    orders = []
    for order in data.get("orders", []):
        orders.append({
            "orderId": order.get("orderId", "N/A"),
            "buyer": order.get("buyer", {}).get("username", "Unknown"),
            "amount": order.get("pricingSummary", {}).get("total", {}).get("value", "0.00"),
            "date": order.get("creationDate", "N/A")
        })

    return jsonify(orders)

# --------------------------------------------------
# 🧠 MANUAL REFRESH ENDPOINT
# --------------------------------------------------
@app.route("/api/ebay/refresh", methods=["POST", "GET"])
def manual_refresh():
    new_token = refresh_access_token()
    if new_token:
        return jsonify({"✅ Token refresh successful": True, "access_token": new_token})
    else:
        return jsonify({"❌ Token refresh failed": True}), 500

# --------------------------------------------------
# STATIC FILES (OPTIONAL)
# --------------------------------------------------
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

# --------------------------------------------------
# 🚀 RUN FLASK APP
# --------------------------------------------------
if __name__ == "__main__":
    print("✅ Flask API Starting — My eBay Dashboard")
    app.run(host="0.0.0.0", port=5000)

