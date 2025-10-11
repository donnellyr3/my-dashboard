import os
import time
import threading
from base64 import b64encode
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# --------------------------
# TEMPORARY IN-MEMORY STORAGE
# --------------------------
products = []
orders = []

# --------------------------
# ROOT / HEALTH
# --------------------------
@app.route("/")
def home():
    return jsonify({"message": "✅ My eBay Dashboard API is live"}), 200


# --------------------------
# REFRESH TEST ENDPOINT
# --------------------------
@app.route("/api/refresh", methods=["POST"])
def refresh_data():
    """Simulate a full data refresh (placeholder)"""
    return jsonify({
        "message": "Sync complete — listings updated!",
        "success": True
    }), 200


# --------------------------
# ADD PRODUCT (mock)
# --------------------------
@app.route("/api/add_product", methods=["POST"])
def add_product():
    data = request.get_json()
    url = data.get("url", "")

    if not url:
        return jsonify({"success": False, "message": "No URL provided"}), 400

    product = {
        "id": f"PRD{len(products)+1:04}",
        "title": "Walmart Product",
        "price": 109.86,
        "stock": 10,
        "status": "Active",
        "image": "https://via.placeholder.com/80",
        "description": "Mock product added manually",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    products.append(product)
    return jsonify({"success": True, "message": "Product added successfully"}), 200


# --------------------------
# LOCAL INVENTORY
# --------------------------
@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    active = len([p for p in products if p["stock"] > 0])
    out_of_stock = len([p for p in products if p["stock"] <= 0])
    return jsonify({
        "active": active,
        "out_of_stock": out_of_stock,
        "products": products
    }), 200


# --------------------------
# ORDERS (mock)
# --------------------------
@app.route("/api/orders", methods=["GET"])
def get_orders():
    data = {
        "count": len(orders),
        "orders": orders or [
            {"buyer": "John Doe", "order_id": "ORD1001", "total": 59.99, "date": "2025-10-11"},
            {"buyer": "Sara K.", "order_id": "ORD1002", "total": 43.50, "date": "2025-10-11"}
        ]
    }
    return jsonify(data), 200


# --------------------------
# EBAY LISTINGS (LIVE)
# --------------------------
@app.route("/api/listings", methods=["GET"])
def get_listings():
    """Pull live listings from eBay Inventory API"""
    try:
        EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")

        if not EBAY_ACCESS_TOKEN:
            return jsonify({"success": False, "message": "Missing eBay access token"}), 401

        headers = {
            "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        ebay_url = "https://api.ebay.com/sell/inventory/v1/inventory_item"
        response = requests.get(ebay_url, headers=headers)

        if response.status_code != 200:
            return jsonify({
                "success": False,
                "message": "eBay API error",
                "error": response.text
            }), 400

        data = response.json()
        listings = []

        for item in data.get("inventoryItems", []):
            product = item.get("product", {})
            title = product.get("title", "No title")
            sku = item.get("sku", "N/A")
            price = item.get("price", {}).get("value", "N/A")
            stock = item.get("availability", {}).get("shipToLocationAvailability", {}).get("quantity", 0)

            listings.append({
                "id": sku,
                "title": title,
                "price": price,
                "stock": stock,
                "status": "Active" if stock > 0 else "Out of Stock"
            })

        return jsonify({"success": True, "listings": listings}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# --------------------------
# EBAY TOKEN AUTO-REFRESH
# --------------------------
def refresh_ebay_token():
    """Auto-refresh eBay access token every 2 hours"""
    while True:
        try:
            client_id = os.getenv("EBAY_CLIENT_ID")
            client_secret = os.getenv("EBAY_CLIENT_SECRET")
            refresh_token = os.getenv("EBAY_REFRESH_TOKEN")

            if not all([client_id, client_secret, refresh_token]):
                print("⚠️ Missing one or more eBay credentials — cannot refresh token.")
                time.sleep(7200)
                continue

            credentials = b64encode(f"{client_id}:{client_secret}".encode()).decode()

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            }

            body = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory"
            }

            response = requests.post(
                "https://api.ebay.com/identity/v1/oauth2/token",
                headers=headers,
                data=body
            )

            if response.status_code == 200:
                data = response.json()
                new_token = data.get("access_token")
                os.environ["EBAY_ACCESS_TOKEN"] = new_token
                print("✅ eBay access token refreshed successfully.")
            else:
                print(f"⚠️ Token refresh failed: {response.text}")

        except Exception as e:
            print(f"❌ Token refresh error: {e}")

        # Sleep 2 hours
        time.sleep(7200)


# Start token refresh background thread
threading.Thread(target=refresh_ebay_token, daemon=True).start()


# --------------------------
# RUN APP
# --------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

