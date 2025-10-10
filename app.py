import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")

@app.route('/')
def home():
    return "✅ eBay Dropshipping API Running — Auto Price/Stock Monitor Ready!"

@app.route('/api/ebay/inventory', methods=['GET'])
def get_inventory():
    headers = {"Authorization": f"Bearer {EBAY_ACCESS_TOKEN}", "Content-Type": "application/json"}
    r = requests.get("https://api.ebay.com/sell/inventory/v1/inventory_item", headers=headers)
    return jsonify(r.json())

@app.route('/api/ebay/update', methods=['POST'])
def update_inventory_item():
    data = request.get_json()
    sku = data.get("sku")
    price = data.get("price")
    quantity = data.get("quantity")

    if not sku:
        return jsonify({"error": "Missing SKU"}), 400

    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "availability": {
            "shipToLocationAvailability": {"quantity": quantity}
        },
        "product": {"title": "Updated via Auto Monitor"},
        "offer": {
            "pricingSummary": {
                "price": {"currency": "USD", "value": price}
            }
        }
    }

    r = requests.put(f"https://api.ebay.com/sell/inventory/v1/inventory_item/{sku}", headers=headers, json=payload)
    return jsonify({"status": r.status_code, "response": r.json()})

@app.route('/api/ebay/refresh', methods=['GET'])
def refresh_token():
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.marketing"
    }

    r = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        data=payload,
        auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if r.status_code != 200:
        return jsonify({"❌ Token refresh failed": r.json()}), 400

    new_token = r.json()["access_token"]
    return jsonify({"✅ Token refresh successful": {"access_token": new_token}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

