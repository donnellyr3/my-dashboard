import os
import time
import requests
import threading
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from dotenv import load_dotenv

# --------------------------------------------------
# 🔧 LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------
load_dotenv()

app = Flask(__name__)
CORS(app)

# --------------------------------------------------
# 🔐 eBay API CREDENTIALS
# --------------------------------------------------
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
# 🔄 REFRESH ACCESS TOKEN FUNCTION
# --------------------------------------------------
def refresh_access_token():
    """Automatically refresh short-term access token using the refresh token."""
    global EBAY_ACCESS_TOKEN

    print("♻️ Refreshing eBay access token...")
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": (
            "https://api.ebay.com/oauth/api_scope "
            "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly "
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly"
        ),
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET),
        )

        if response.status_code == 200:
            EBAY_ACCESS_TOKEN = response.json().get("access_token")
            os.environ["EBAY_ACCESS_TOKEN"] = EBAY_ACCESS_TOKEN
            print("✅ Token refreshed successfully.")
            return EBAY_ACCESS_TOKEN
        else:
            print("❌ Token refresh failed:", response.text)
            return None
    except Exception as e:
        print("❌ Exception during token refresh:", e)
        return None

# --------------------------------------------------
# 🔁 AUTO REFRESH LOOP (every 2 hours)
# --------------------------------------------------
def auto_refresh_loop():
    while True:
        refresh_access_token()
        time.sleep(7200)  # every 2 hours

threading.Thread(target=auto_refresh_loop, daemon=True).start()

# --------------------------------------------------
# 📦 GET INVENTORY ENDPOINT
# --------------------------------------------------
@app.route("/api/ebay/inventory", methods=["GET"])
def get_inventory():
    """Fetch eBay inventory items."""
    global EBAY_ACCESS_TOKEN

    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    url = "https://api.ebay.com/sell/inventory/v1/inventory_item"

    response = requests.get(url, headers=headers)

    # Handle expired token
    if response.status_code == 401:
        refresh_access_token()
        headers["Authorization"] = f"Bearer {EBAY_ACCESS_TOKEN}"
        response = requests.get(url, headers=headers)

    # eBay API failed → fallback mock data
    if response.status_code != 200:
        print("⚠️ eBay API failed, serving mock data instead.")
        return jsonify([
            {"image": "https://via.placeholder.com/60", "title": "Wireless Mouse", "price": "12.99", "stock": 25, "status": "Active"},
            {"image": "https://via.placeholder.com/60", "title": "Gaming Keyboard", "price": "34.99", "stock": 10, "status": "Low Stock"},
            {"image": "https://via.placeholder.com/60", "title": "HD Webcam", "price": "49.99", "stock": 0, "status": "Out of Stock"}
        ])

    # Parse eBay inventory
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
# 🧾 GET ORDERS ENDPOINT
# --------------------------------------------------
@app.route("/api/ebay/orders", methods=["GET"])
def get_orders():
    """Fetch eBay orders."""
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
        print("⚠️ eBay orders request failed, serving mock orders.")
        return jsonify([
            {"orderId": "EBAY12345", "buyer": "John D.", "amount": "45.99", "date": "2025-10-05"},
            {"orderId": "EBAY12346", "buyer": "Sara K.", "amount": "22.50", "date": "2025-10-06"}
        ])

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
# 🔁 MANUAL REFRESH ENDPOINT (FIXED VERSION)
# --------------------------------------------------
@app.route("/api/ebay/refresh", methods=["GET", "POST"])
def manual_refresh():
    """Manually trigger token refresh via eBay OAuth2 endpoint."""
    global EBAY_ACCESS_TOKEN

    print("♻️ Manual token refresh requested...")

    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": (
            "https://api.ebay.com/oauth/api_scope "
            "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly "
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly"
        )
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET)
        )

        if response.status_code == 200:
            new_token = response.json().get("access_token")
            EBAY_ACCESS_TOKEN = new_token
            os.environ["EBAY_ACCESS_TOKEN"] = new_token
            print("✅ Token refresh successful!")
            return jsonify({
                "success": True,
                "message": "✅ Token refresh successful!",
                "access_token": new_token
            })
        else:
            print("❌ eBay token refresh failed:", response.text)
            return jsonify({
                "success": False,
                "status": response.status_code,
                "error": response.text
            }), response.status_code

    except Exception as e:
        print("❌ Exception during token refresh:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# --------------------------------------------------
# 🌐 STATIC FILES (OPTIONAL)
# --------------------------------------------------
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

# --------------------------------------------------
# 🚀 RUN APP
# --------------------------------------------------
if __name__ == "__main__":
    print("✅ Flask API Starting — My eBay Dashboard")
    app.run(host="0.0.0.0", port=5000)

