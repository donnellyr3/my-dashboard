import os
import json
import random
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

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


# --- ADD NEW PRODUCT ---
@app.route("/api/add_product", methods=["POST"])
def add_product():
    """Adds a new mock product to data/products.json"""
    try:
        data = request.get_json()

        # Validation
        if not data or "title" not in data or "url" not in data:
            return jsonify({"error": "Missing required fields"}), 400

        products = load_products()
        new_item = {
            "id": f"WM{str(len(products)+1).zfill(3)}",
            "title": data.get("title"),
            "url": data.get("url"),
            "image": data.get("image", "https://via.placeholder.com/80"),
            "price": float(data.get("price", 0)),
            "stock": int(data.get("stock", 0)),
            "status": "Active" if int(data.get("stock", 0)) > 0 else "Out of Stock",
        }

        products.append(new_item)
        save_products(products)

        return jsonify({
            "message": "✅ Product added successfully!",
            "product": new_item,
            "success": True
        })
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

