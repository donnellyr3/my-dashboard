import os
import json
import random
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from threading import Timer

# ============================================================
# Flask Setup
# ============================================================
app = Flask(__name__)
CORS(app)

DATA_PATH = "data/products.json"

# ============================================================
# Root endpoint (for testing Render connection)
# ============================================================
@app.route("/")
def home():
    return jsonify({
        "response": "✅ eBay Dropshipping API Running — Auto Price/Stock Monitor Ready!"
    })

# ============================================================
# Inventory endpoint (mock Walmart data)
# ============================================================
@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    try:
        with open(DATA_PATH, "r") as f:
            products = json.load(f)
    except Exception as e:
        return jsonify({"error": f"Could not load products.json: {str(e)}"}), 500

    return jsonify({
        "count": len(products),
        "products": products
    })

# ============================================================
# Orders endpoint (mock eBay-style order list)
# ============================================================
@app.route("/api/orders", methods=["GET"])
def get_orders():
    mock_orders = [
        {"order_id": "ORD001", "buyer": "John Doe", "date": "2025-10-09", "total": 79.99},
        {"order_id": "ORD002", "buyer": "Sara K.", "date": "2025-10-10", "total": 45.50},
        {"order_id": "ORD003", "buyer": "Liam R.", "date": "2025-10-11", "total": 65.00},
    ]
    return jsonify({"count": len(mock_orders), "orders": mock_orders})

# ============================================================
# Sync endpoint (mock Walmart "Refresh" automation)
# ============================================================
@app.route("/api/sync", methods=["GET", "POST"])
def sync_products():
    """Simulates auto price/stock sync like AutoDS"""
    try:
        with open(DATA_PATH, "r") as f:
            products = json.load(f)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    # Update prices & stock randomly
    for p in products:
        p["price"] = round(random.uniform(35, 100), 2)
        p["stock"] = random.randint(0, 30)
        p["status"] = "Active" if p["stock"] > 0 else "Out of Stock"

    # Save changes
    with open(DATA_PATH, "w") as f:
        json.dump(products, f, indent=2)

    return jsonify({
        "success": True,
        "message": f"✅ Sync completed — {len(products)} products updated (mock mode)",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

# ============================================================
# Auto-refresh (every 90 minutes)
# ============================================================
def auto_refresh():
    try:
        print("🔄 Auto-refresh triggered (mock sync running...)")
        sync_products()
    except Exception as e:
        print("Auto-refresh error:", e)
    Timer(5400, auto_refresh).start()  # 5400 sec = 90 min

Timer(10, auto_refresh).start()

# ============================================================
# Run Flask app
# ============================================================
if __name__ == "__main__":
    print("✅ Flask API started — Walmart mock automation ready!")
    app.run(host="0.0.0.0", port=5000)

