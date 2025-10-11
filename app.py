from flask import Flask, request, jsonify
import json
import os
import random

app = Flask(__name__)

DATA_FILE = "products.json"

# ------------------------
# Utility functions
# ------------------------
def load_products():
    """Load all products from file."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    """Save all products to file."""
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=2)

def detect_store(url):
    """Mock store detection and scraping (replace later with real logic)."""
    # This simulates product info for any URL.
    return {
        "title": "Sample Product from " + url,
        "image": "https://via.placeholder.com/80",
        "description": "Mock scraped product info",
        "price": round(random.uniform(20.0, 100.0), 2),
        "stock": random.randint(1, 25),
    }

# ------------------------
# ROUTES
# ------------------------

@app.route("/", methods=["GET"])
def home():
    """Basic status check."""
    return jsonify({"response": "✅ Universal Dropshipping API Running — Auto Product Import Ready!"})


@app.route("/api/add_product", methods=["POST"])
def add_product():
    """Add new product from a given URL."""
    try:
        data = request.get_json()
        url = data.get("url")

        if not url:
            return jsonify({"error": "Missing product URL"}), 400

        scraped = detect_store(url)

        products = load_products()
        new_item = {
            "id": f"PRD{str(len(products)+1).zfill(3)}",
            "url": url,
            "title": scraped["title"],
            "image": scraped["image"],
            "description": scraped["description"],
            "price": scraped["price"],
            "stock": scraped["stock"],
            "status": "Active"
        }
        products.append(new_item)
        save_products(products)

        return jsonify({"message": "✅ Product imported successfully!", "product": new_item})

    except Exception as e:
        print(f"Error in /api/add_product: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/get_listings", methods=["GET"])
def get_listings():
    """Return all products."""
    products = load_products()
    return jsonify({"products": products, "count": len(products)})


@app.route("/api/refresh_data", methods=["GET"])
def refresh_data():
    """Simulate inventory refresh."""
    products = load_products()
    for p in products:
        p["stock"] = max(0, p["stock"] - random.randint(0, 2))
        p["status"] = "Active" if p["stock"] > 0 else "Out of Stock"
    save_products(products)
    return jsonify({"message": "Inventory refreshed!", "products": products})


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    """Return summarized inventory stats."""
    products = load_products()
    total = len(products)
    active = len([p for p in products if p["status"] == "Active"])
    out_of_stock = total - active

    return jsonify({
        "total": total,
        "active": active,
        "out_of_stock": out_of_stock,
        "products": products
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

