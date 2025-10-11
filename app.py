import os
import csv
import requests
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from bs4 import BeautifulSoup
import sqlite3
import io

app = Flask(__name__)
CORS(app)

# ==============================
# CONFIG & ENVIRONMENT
# ==============================
DB_PATH = os.getenv("DB_PATH", "products.db")
API_KEY = os.getenv("API_KEY", "secret123")
PRICE_MARKUP_PCT = float(os.getenv("PRICE_MARKUP_PCT", "0.18"))
PRICE_FLAT_FEE = float(os.getenv("PRICE_FLAT_FEE", "3.0"))
TREAT_UNKNOWN_STOCK_OOS = bool(int(os.getenv("TREAT_UNKNOWN_STOCK_OOS", "0")))

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")

# ==============================
# DATABASE SETUP
# ==============================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            price REAL,
            stock INTEGER,
            date_added TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==============================
# HELPERS
# ==============================
def authorized(req):
    auth_header = req.headers.get("Authorization", "")
    return auth_header == f"Bearer {API_KEY}"

def scrape_product(url):
    """Basic universal product scraper (placeholder)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        page = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(page.text, "lxml")

        title = soup.find("title").get_text() if soup.find("title") else "Unknown Product"
        price = 19.99
        stock = 10

        return {
            "title": title.strip(),
            "price": round(price + (price * PRICE_MARKUP_PCT) + PRICE_FLAT_FEE, 2),
            "stock": stock,
            "url": url
        }
    except Exception as e:
        return {"error": str(e), "url": url}

# ==============================
# ROUTES
# ==============================

@app.route("/")
def home():
    return jsonify({"response": "✅ Universal Dropshipping API Running — Auto Product Import Ready!"})

@app.route("/api/config")
def config():
    return jsonify({
        "DB_PATH": DB_PATH,
        "PRICE_MARKUP_PCT": PRICE_MARKUP_PCT,
        "PRICE_FLAT_FEE": PRICE_FLAT_FEE,
        "TREAT_UNKNOWN_STOCK_OOS": TREAT_UNKNOWN_STOCK_OOS
    })

# --- ADD SINGLE PRODUCT ---
@app.route("/api/add_product", methods=["POST"])
def add_product():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    product = scrape_product(url)
    if "error" in product:
        return jsonify(product), 400

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (title, url, price, stock, date_added) VALUES (?, ?, ?, ?, ?)",
        (product["title"], url, product["price"], product["stock"], datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Product added successfully"})

# --- BULK ADD ---
@app.route("/api/bulk_add", methods=["POST"])
def bulk_add():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    urls = data.get("urls", [])
    results = []
    for url in urls:
        product = scrape_product(url)
        if "error" not in product:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO products (title, url, price, stock, date_added) VALUES (?, ?, ?, ?, ?)",
                (product["title"], url, product["price"], product["stock"], datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()
        results.append(product)
    return jsonify({"added": results})

# --- FIXED: LISTINGS ---
@app.route("/api/listings", methods=["GET"])
def listings():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    conn.close()

    products = []
    for r in rows:
        products.append({
            "id": r[0],
            "title": r[1],
            "url": r[2],
            "price": r[3],
            "stock": r[4],
            "date_added": r[5]
        })
    return jsonify({"count": len(products), "products": products})

# --- DELETE SINGLE PRODUCT ---
@app.route("/api/delete_product/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Product {pid} deleted"})

# --- BULK DELETE ---
@app.route("/api/bulk_delete", methods=["POST"])
def bulk_delete():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    ids = data.get("ids", [])
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executemany("DELETE FROM products WHERE id=?", [(i,) for i in ids])
    conn.commit()
    conn.close()
    return jsonify({"success": True, "deleted": len(ids)})

# --- EXPORT CSV ---
@app.route("/api/export", methods=["GET"])
def export_csv():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "title", "url", "price", "stock", "date_added"])
    writer.writerows(rows)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="products_export.csv"
    )

# --- INVENTORY SUMMARY ---
@app.route("/api/inventory", methods=["GET"])
def inventory_summary():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(CASE WHEN stock=0 THEN 1 ELSE 0 END) FROM products")
    total, oos = cur.fetchone()
    conn.close()
    return jsonify({"total": total, "out_of_stock": oos})

# --- MOCK ORDERS ---
@app.route("/api/orders", methods=["GET"])
def mock_orders():
    data = {
        "count": 2,
        "orders": [
            {"buyer": "John Doe", "date": "2025-10-11", "order_id": "ORD1001", "total": 59.99},
            {"buyer": "Sara K.", "date": "2025-10-11", "order_id": "ORD1002", "total": 43.50}
        ]
    }
    return jsonify(data)

# --- REFRESH DATA MOCK ---
@app.route("/api/refresh_data", methods=["POST"])
def refresh_data():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"success": True, "message": "Stock & pricing refreshed"})

# ==============================
# EBAY AUTH MANAGEMENT
# ==============================
@app.route("/api/status", methods=["GET"])
def ebay_status():
    return jsonify({
        "client_id_set": bool(EBAY_CLIENT_ID),
        "client_secret_set": bool(EBAY_CLIENT_SECRET),
        "refresh_token_set": bool(EBAY_REFRESH_TOKEN),
        "access_token_set": bool(EBAY_ACCESS_TOKEN),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@app.route("/api/check_token", methods=["GET"])
def ebay_check_token():
    token = os.getenv("EBAY_ACCESS_TOKEN")
    if not token:
        return jsonify({"success": False, "message": "No access token found"}), 400

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.get("https://api.ebay.com/sell/account/v1/privilege", headers=headers, timeout=10)
        if r.status_code == 200:
            return jsonify({"success": True, "message": "Access token is valid", "status_code": 200})
        else:
            return jsonify({
                "success": False,
                "message": "Invalid or expired access token",
                "status_code": r.status_code,
                "response": r.text
            })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/refresh_token", methods=["GET"])
def refresh_token():
    if not all([EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_REFRESH_TOKEN]):
        return jsonify({"success": False, "message": "Missing one or more eBay credentials"}), 400

    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {requests.utils.quote(EBAY_CLIENT_ID + ':' + EBAY_CLIENT_SECRET)}"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": EBAY_REFRESH_TOKEN,
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        r = requests.post("https://api.ebay.com/identity/v1/oauth2/token", headers=headers, data=data, timeout=10)
        if r.status_code == 200:
            res = r.json()
            os.environ["EBAY_ACCESS_TOKEN"] = res.get("access_token", "")
            return jsonify({**res, "message": "Access token refreshed successfully", "success": True})
        else:
            return jsonify({
                "success": False,
                "message": "Failed to refresh token",
                "response": r.text,
                "status_code": r.status_code
            })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==============================
# DEBUG ROUTE MAP
# ==============================
print("\n🔍 Registered routes:")
for rule in app.url_map.iter_rules():
    print(rule)
print("✅ Flask app initialized successfully!\n")

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

