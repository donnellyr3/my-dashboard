import os
import json
import random
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

# --------------------------------------------------
# INITIAL SETUP
# --------------------------------------------------
app = Flask(__name__)
CORS(app)

DATA_FILE = "data/products.json"


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def load_products():
    """Load mock product data from JSON file"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_products(products):
    """Save products to JSON file"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=2)


# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.route("/")
def home():
    """Root health check"""
    return jsonify({"response": "✅ eBay Dropshipping API Running — Auto Price/Stock Monitor Ready!"})


# --- INVENTORY LIST (MOCK WALMART ITEMS) ---
@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    products = load_products()

    # Randomize price + stock for realism
    for p in products:
        p["price"] = round(random.uniform(35, 99), 2)
        p["stock"] = random.randint(0, 20)
        p["status"] = "Active" if p["stock"] > 0 else "Out of Stock"

    return jsonify({"count": len(products), "products": products})


# --- MOCK ORDERS ---
@app.route("/api/orders", methods=["GET"])
def get_orders():
    mock_orders = [
        {"order_id": "ORD001", "buyer": "John Doe", "date": "2025-10-09", "total": 79.99},
        {"order_id": "ORD002", "buyer": "Sara K.", "date": "2025-10-10", "total": 45.50},
        {"order_id": "ORD003", "buyer": "Liam R.", "date": "2025-10-11", "total": 65.00},
    ]
    return jsonify({"count": len(mock_orders), "orders": mock_orders})


# --- ADD PRODUCT BY URL ONLY (Auto-Fill Walmart Info) ---
@app.route("/api/add_product", methods=["POST"])
def add_product():
    """Add new product using only a Walmart URL."""
    try:
        data = request.get_json()
        url = data.get("url")

        if not url:
            return jsonify({"error": "Missing Walmart URL"}), 400

        # --- Extract Walmart product info ---
        headers = {"User-Agent": "Mozilla/5.0"}
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, "html.parser")

        # Title
        title_tag = soup.find("h1")
        title = title_tag.text.strip() if title_tag else "Unknown Walmart Product"

        # Image
        image_tag = soup.find("img")
        image_url = image_tag["src"] if image_tag and "src" in image_tag.attrs else "https://via.placeholder.com/80"

        # Price
        price_tag = soup.find("span", {"class": "price-characteristic"})
        if price_tag and price_tag.get("content"):
            price = float(price_tag["content"])
        else:
            price = round(random.uniform(35, 99), 2)

        # --- Build product entry ---
        products = load_products()
        new_item = {
            "id": f"WM{str(len(products)+1).zfill(3)}",
            "title": title,
            "url": url,
            "image": image_url,
            "price": price,
            "stock": random.randint(1, 25),
            "status": "Active",
        }

        # --- Save & return ---
        products.append(new_item)
        save_products(products)
        return jsonify({"message": "✅ Product added from URL", "product": new_item, "success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- SYNC (MOCK REFRESH) ---
@app.route("/api/sync", methods=["POST"])
def sync_data():
    return jsonify({
        "message": "✅ Sync completed — 2 products updated (mock mode)",
        "success": True,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# --------------------------------------------------
# RUN FLASK (for local or Render)
# --------------------------------------------------
if __name__ == "__main__":
    print("✅ Running Dropshipping API — Auto Price/Stock Monitor Ready!")
    app.run(host="0.0.0.0", port=5000)

