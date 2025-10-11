import os
import json
import random
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from threading import Timer

app = Flask(__name__)
CORS(app)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "products.json")

def load_products():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load products.json: {e}")
        return []

def simulate_walmart_data(products):
    simulated = []
    for item in products:
        price = round(random.uniform(35.0, 99.0), 2)
        stock = random.randint(0, 30)
        simulated.append({
            "id": item.get("id"),
            "title": item.get("title", f"Mock Product {item.get('id', '')}"),
            "url": item.get("url"),
            "price": price,
            "stock": stock,
            "status": "Active" if stock > 0 else "Out of Stock",
            "image": item.get("image", "https://via.placeholder.com/80")
        })
    return simulated

@app.route("/")
def home():
    return jsonify({
        "message": "✅ Walmart Dropshipping Mock API Running — AutoDS Clone Ready",
        "endpoints": ["/api/inventory", "/api/orders", "/api/sync"]
    })

@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    products = load_products()
    data = simulate_walmart_data(products)
    return jsonify({"count": len(data), "products": data})

@app.route("/api/orders", methods=["GET"])
def get_orders():
    mock_orders = [
        {"order_id": "ORD001", "buyer": "John Doe", "total": 79.99, "date": "2025-10-09"},
        {"order_id": "ORD002", "buyer": "Sara K.", "total": 45.50, "date": "2025-10-10"},
        {"order_id": "ORD003", "buyer": "Liam R.", "total": 65.00, "date": "2025-10-11"},
    ]
    return jsonify({"count": len(mock_orders), "orders": mock_orders})

@app.route("/api/sync", methods=["POST"])
def sync_prices():
    products = load_products()
    updated_data = simulate_walmart_data(products)
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(updated_data, f, indent=2)
    except Exception as e:
        print("⚠️ Could not write to products.json:", e)

    return jsonify({
        "success": True,
        "message": f"✅ Sync completed — {len(updated_data)} products updated (mock mode)",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

def auto_sync_loop():
    try:
        print("🔄 Auto-sync triggered (mock mode)...")
        load_products()
    except Exception as e:
        print("Auto-sync error:", e)
    Timer(5400, auto_sync_loop).start()

Timer(10, auto_sync_loop).start()

if __name__ == "__main__":
    print("✅ Walmart Dropshipping Mock API Running — Ready for Appsmith connection")
    app.run(host="0.0.0.0", port=5000)

