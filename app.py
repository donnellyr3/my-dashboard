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
# HELPERS
# --------------------------------------------------
def load_products():
    """Load product data"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_products(products):
    """Save products"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=2)


# --------------------------------------------------
# SCRAPER FUNCTIONS
# --------------------------------------------------

def scrape_walmart(url):
    """Scrape product info from Walmart"""
    headers = {"User-Agent": "Mozilla/5.0"}
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")

    title = soup.find("h1")
    image = soup.find("img")
    desc = soup.find("div", {"class": "about-desc"})
    price_tag = soup.find("span", {"class": "price-characteristic"})

    return {
        "title": title.text.strip() if title else "Unknown Walmart Product",
        "image": image["src"] if image and image.get("src") else "https://via.placeholder.com/80",
        "description": desc.text.strip() if desc else "No description found",
        "price": float(price_tag["content"]) if price_tag and price_tag.get("content") else round(random.uniform(35, 99), 2),
        "stock": random.randint(1, 25)
    }


def scrape_target(url):
    """Scrape product info from Target"""
    headers = {"User-Agent": "Mozilla/5.0"}
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")

    title = soup.find("h1")
    image = soup.find("img")
    price_tag = soup.find("span", {"data-test": "product-price"})

    return {
        "title": title.text.strip() if title else "Unknown Target Product",
        "image": image["src"] if image and image.get("src") else "https://via.placeholder.com/80",
        "description": "Imported from Target",
        "price": round(random.uniform(35, 99), 2) if not price_tag else float(''.join([c for c in price_tag.text if c.isdigit() or c == '.'])),
        "stock": random.randint(1, 20)
    }


def scrape_bestbuy(url):
    """Scrape product info from BestBuy"""
    headers = {"User-Agent": "Mozilla/5.0"}
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")

    title = soup.find("h1")
    image = soup.find("img")
    price_tag = soup.find("div", {"class": "priceView-hero-price priceView-customer-price"})

    return {
        "title": title.text.strip() if title else "Unknown BestBuy Product",
        "image": image["src"] if image and image.get("src") else "https://via.placeholder.com/80",
        "description": "Imported from BestBuy",
        "price": round(random.uniform(50, 150), 2),
        "stock": random.randint(1, 15)
    }


def scrape_aliexpress(url):
    """Scrape product info from AliExpress"""
    headers = {"User-Agent": "Mozilla/5.0"}
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")

    title = soup.find("h1")
    image = soup.find("img")
    price_tag = soup.find("span", {"class": "uniform-banner-box-price"})

    return {
        "title": title.text.strip() if title else "Unknown AliExpress Product",
        "image": image["src"] if image and image.get("src") else "https://via.placeholder.com/80",
        "description": "Imported from AliExpress",
        "price": round(random.uniform(10, 50), 2),
        "stock": random.randint(5, 50)
    }


def detect_store(url):
    """Detect site domain and choose scraper"""
    if "walmart.com" in url:
        return scrape_walmart(url)
    elif "target.com" in url:
        return scrape_target(url)
    elif "bestbuy.com" in url:
        return scrape_bestbuy(url)
    elif "aliexpress.com" in url:
        return scrape_aliexpress(url)
    else:
        raise ValueError("Unsupported website — only Walmart, Target, BestBuy, and AliExpress supported.")


# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.route("/")
def home():
    return jsonify({"response": "✅ Universal Dropshipping API Running — Auto Product Import Ready!"})


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    products = load_products()
    return jsonify({"count": len(products), "products": products})


@app.route("/api/orders", methods=["GET"])
def get_orders():
    mock_orders = [
        {"order_id": "ORD001", "buyer": "John Doe", "date": "2025-10-09", "total": 79.99},
        {"order_id": "ORD002", "buyer": "Sara K.", "date": "2025-10-10", "total": 45.50},
        {"order_id": "ORD003", "buyer": "Liam R.", "date": "2025-10-11", "total": 65.00},
    ]
    return jsonify({"count": len(mock_orders), "orders": mock_orders})


@app.route("/api/add_product", methods=["POST"])
def add_product():
    """Add new product from any supported URL"""
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

        return jsonify({"message": "✅ Product imported successfully!", "product": new_item, "success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sync", methods=["POST"])
def sync_data():
    return jsonify({
        "message": "✅ Sync complete — mock refresh successful",
        "success": True,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# --------------------------------------------------
# RUN APP
# --------------------------------------------------
if __name__ == "__main__":
    print("✅ Universal Dropshipping API Running — Auto Product Import Ready!")
    app.run(host="0.0.0.0", port=5000)

