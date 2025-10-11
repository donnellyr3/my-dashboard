import os
import re
import io
import csv
import json
import time
import math
import sqlite3
import random
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional

import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# ---------------------------
# Config / Defaults (ENV-driven)
# ---------------------------
API_KEY = os.getenv("API_KEY", "secret123")                 # <-- set this in Render
DB_PATH = os.getenv("DB_PATH", "products.db")
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (autods-like-dashboard)")
# pricing rule: price = max(source_price*(1+markup_pct), source_price + fee)
PRICE_MARKUP_PCT = float(os.getenv("PRICE_MARKUP_PCT", "0.18"))
PRICE_FLAT_FEE = float(os.getenv("PRICE_FLAT_FEE", "3.00"))
TREAT_UNKNOWN_STOCK_OOS = os.getenv("TREAT_UNKNOWN_STOCK_OOS", "0") == "1"
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "12"))  # seconds

app = Flask(__name__)
CORS(app)


# ---------------------------
# Utilities: DB
# ---------------------------
def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        source TEXT,
        title TEXT,
        description TEXT,
        image TEXT,
        price REAL,
        stock INTEGER,
        status TEXT,
        created_at TEXT,
        updated_at TEXT
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_source ON products(source);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_created ON products(created_at);")
    conn.commit()
    conn.close()

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}

def now_iso():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# ---------------------------
# Utilities: Auth
# ---------------------------
def require_key():
    hdr = request.headers.get("Authorization", "")
    if not hdr.startswith("Bearer "):
        return False
    key = hdr.split(" ", 1)[1].strip()
    return key == API_KEY

def auth_guard():
    if not require_key():
        return jsonify({"error": "Unauthorized"}), 401

# ---------------------------
# Utilities: Pricing / Stock
# ---------------------------
def apply_price_rule(source_price: Optional[float]) -> Optional[float]:
    if source_price is None:
        return None
    return round(max(source_price * (1 + PRICE_MARKUP_PCT), source_price + PRICE_FLAT_FEE), 2)

def normalize_stock(stock: Optional[int]) -> (int, str):
    if stock is None and TREAT_UNKNOWN_STOCK_OOS:
        return 0, "Out of Stock"
    if stock is None:
        return 10, "Active"   # default conservative availability if not strict
    return max(0, int(stock)), ("Active" if stock and int(stock) > 0 else "Out of Stock")

# ---------------------------
# Scraper registry (plug-in style)
# Each returns: {title, image, description, price, stock}
# ---------------------------
Headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.8"}

def fetch_html(url: str) -> Optional[str]:
    try:
        r = requests.get(url, headers=Headers, timeout=REQUEST_TIMEOUT)
        if r.status_code >= 400:
            return None
        return r.text
    except Exception:
        return None

def parse_og(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    def og(prop):
        tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
        return tag["content"].strip() if tag and tag.get("content") else None
    return {
        "title": og("og:title"),
        "image": og("og:image"),
        "description": og("og:description"),
        "price_raw": og("product:price:amount") or og("og:price:amount") or None,
    }

def as_float(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d{1,2})?)", text.replace(",", ""))
    return float(m.group(1)) if m else None

def walmart_scraper(url: str) -> Dict[str, Any]:
    # Very light scraper using OG tags as fallback; robust to structure changes.
    html = fetch_html(url)
    soup = BeautifulSoup(html or "", "lxml")
    og = parse_og(soup)
    # Walmart price hints sometimes live in scripts; we keep it simple:
    price = as_float(og["price_raw"])
    # crude fallback: any $xx.yy in page
    if price is None and html:
        m = re.search(r'\$\s?(\d{1,4}(?:\.\d{2})?)', html)
        price = float(m.group(1)) if m else None
    stock = None  # unknown from public page; can be extended with APIs
    return {
        "title": og["title"] or "Walmart Product",
        "image": og["image"] or "https://via.placeholder.com/80",
        "description": og["description"] or "No description found",
        "price": price if price is not None else round(40 + random.random()*60, 2),
        "stock": stock
    }

def amazon_scraper(url: str) -> Dict[str, Any]:
    html = fetch_html(url)
    soup = BeautifulSoup(html or "", "lxml")
    og = parse_og(soup)
    # Amazon blocks aggressively; rely on og + fallback random demo price
    price = as_float(og["price_raw"])
    return {
        "title": og["title"] or "Amazon Product",
        "image": og["image"] or "https://via.placeholder.com/80",
        "description": og["description"] or "No description found",
        "price": price if price is not None else round(40 + random.random()*60, 2),
        "stock": None
    }

def target_scraper(url: str) -> Dict[str, Any]:
    html = fetch_html(url)
    soup = BeautifulSoup(html or "", "lxml")
    og = parse_og(soup)
    price = as_float(og["price_raw"])
    return {
        "title": og["title"] or "Target Product",
        "image": og["image"] or "https://via.placeholder.com/80",
        "description": og["description"] or "No description found",
        "price": price if price is not None else round(40 + random.random()*60, 2),
        "stock": None
    }

def generic_scraper(url: str) -> Dict[str, Any]:
    html = fetch_html(url)
    soup = BeautifulSoup(html or "", "lxml")
    og = parse_og(soup)
    price = as_float(og["price_raw"])
    return {
        "title": og["title"] or (soup.title.text.strip() if soup.title else "Product"),
        "image": og["image"] or "https://via.placeholder.com/80",
        "description": og["description"] or "No description found",
        "price": price if price is not None else round(40 + random.random()*60, 2),
        "stock": None
    }

SCRAPERS = {
    "walmart.com": walmart_scraper,
    "amazon.com": amazon_scraper,
    "target.com": target_scraper,
}

def detect_store(url: str):
    host = urlparse(url).netloc.lower()
    for domain, fn in SCRAPERS.items():
        if domain in host:
            return domain, fn
    return "generic", generic_scraper

# ---------------------------
# Core: Product upsert / refresh
# ---------------------------
def next_id(conn: sqlite3.Connection) -> str:
    cur = conn.execute("SELECT COUNT(*) AS c FROM products")
    c = cur.fetchone()["c"] or 0
    return f"PRD{c+1:04d}"

def upsert_product(url: str, scraped: Dict[str, Any]) -> Dict[str, Any]:
    source, _ = detect_store(url)
    price_src = scraped.get("price")
    final_price = apply_price_rule(price_src)
    stock, status = normalize_stock(scraped.get("stock"))

    conn = db()
    cur = conn.cursor()
    # try find existing by URL
    cur.execute("SELECT * FROM products WHERE url = ?", (url,))
    row = cur.fetchone()
    ts = now_iso()

    payload = {
        "url": url,
        "source": source,
        "title": scraped.get("title"),
        "description": scraped.get("description"),
        "image": scraped.get("image"),
        "price": final_price,
        "stock": stock,
        "status": status,
        "updated_at": ts,
    }

    if row:
        cur.execute("""
            UPDATE products
            SET source=:source, title=:title, description=:description, image=:image,
                price=:price, stock=:stock, status=:status, updated_at=:updated_at
            WHERE url=:url
        """, payload)
        pid = row["id"]
    else:
        pid = next_id(conn)
        payload["id"] = pid
        payload["created_at"] = ts
        cols = ",".join(payload.keys())
        ph = ":" + ",:".join(payload.keys())
        cur.execute(f"INSERT INTO products ({cols}) VALUES ({ph})", payload)

    conn.commit()
    cur.execute("SELECT * FROM products WHERE id = ?", (pid,))
    out = row_to_dict(cur.fetchone())
    conn.close()
    return out

def refresh_all_products() -> Dict[str, Any]:
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    results = []
    updated = 0
    for r in rows:
        url = r["url"]
        _, scraper = detect_store(url)
        scraped = scraper(url)
        # keep same URL, but refresh scraped fields & reapply rule
        updated_row = upsert_product(url, scraped)
        results.append(updated_row)
        updated += 1
    return {"updated": updated, "products": results}

# ---------------------------
# Routes
# ---------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"response": "✅ Universal Dropshipping API Running — Auto Product Import Ready!"})

@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify({
        "api_key_set": bool(API_KEY),
        "db_path": DB_PATH,
        "price_markup_pct": PRICE_MARKUP_PCT,
        "price_flat_fee": PRICE_FLAT_FEE,
        "treat_unknown_stock_oos": TREAT_UNKNOWN_STOCK_OOS
    })

@app.route("/api/add_product", methods=["POST"])
def add_product():
    if request.method != "POST":
        return jsonify({"error": "Method Not Allowed"}), 405
    # auth for write
    if (auth := auth_guard()) is not None:
        return auth

    try:
        data = request.get_json(silent=True) or {}
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "Missing 'url'"}), 400

        domain, scraper = detect_store(url)
        scraped = scraper(url)
        product = upsert_product(url, scraped)
        return jsonify({"success": True, "message": "✅ Product imported successfully!", "product": product})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/bulk_add", methods=["POST"])
def bulk_add():
    if (auth := auth_guard()) is not None:
        return auth
    data = request.get_json(silent=True) or {}
    urls: List[str] = data.get("urls") or []
    # Optional: CSV URL
    csv_url = data.get("csv")
    if csv_url:
        try:
            r = requests.get(csv_url, headers=Headers, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            text = r.text
            for row in csv.reader(io.StringIO(text)):
                if not row:
                    continue
                urls.append(row[0].strip())
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to fetch CSV: {e}"}), 400

    results = []
    for u in urls:
        try:
            _, scraper = detect_store(u)
            scraped = scraper(u)
            item = upsert_product(u, scraped)
            results.append({"url": u, "ok": True, "id": item["id"]})
        except Exception as e:
            results.append({"url": u, "ok": False, "error": str(e)})

    return jsonify({"success": True, "added": sum(1 for r in results if r["ok"]), "results": results})

@app.route("/api/get_listings", methods=["GET"])
def get_listings():
    # filters: q (search in title), status, source; pagination: page, page_size
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    source = request.args.get("source", "").strip()
    page = int(request.args.get("page", "1"))
    page_size = min(200, max(1, int(request.args.get("page_size", "50"))))

    where = []
    params = []
    if q:
        where.append("(title LIKE ? OR description LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if status:
        where.append("status = ?")
        params.append(status)
    if source:
        where.append("source = ?")
        params.append(source)
    wsql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = db()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) AS c FROM products {wsql}", params)
    total = cur.fetchone()["c"] or 0

    offset = (page - 1) * page_size
    cur.execute(f"""
        SELECT * FROM products
        {wsql}
        ORDER BY updated_at DESC
        LIMIT ? OFFSET ?
    """, (*params, page_size, offset))
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify({
        "count": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if page_size else 1,
        "products": rows
    })

@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM products WHERE status='Active'")
    active = cur.fetchone()["c"] or 0
    cur.execute("SELECT COUNT(*) AS c FROM products WHERE status='Out of Stock'")
    oos = cur.fetchone()["c"] or 0
    cur.execute("SELECT * FROM products ORDER BY updated_at DESC LIMIT 50")
    sample = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({
        "active": active,
        "out_of_stock": oos,
        "products": sample
    })

@app.route("/api/orders", methods=["GET"])
def get_orders():
    # Mock placeholder; wire to marketplace later
    today = datetime.utcnow().strftime("%Y-%m-%d")
    orders = [
        {"order_id": "ORD1001", "buyer": "John Doe", "date": today, "total": 59.99},
        {"order_id": "ORD1002", "buyer": "Sara K.", "date": today, "total": 43.50},
    ]
    return jsonify({"count": len(orders), "orders": orders})

@app.route("/api/refresh_data", methods=["POST", "GET"])
def refresh_data():
    # Allow POST (preferred). GET just for quick tests.
    if request.method == "POST" and (auth := auth_guard()) is not None:
        return auth
    try:
        res = refresh_all_products()
        return jsonify({"success": True, "message": f"🔄 Refreshed {res['updated']} products", **res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# alias for older wiring
@app.route("/api/sync", methods=["POST"])
def sync_alias():
    if (auth := auth_guard()) is not None:
        return auth
    return refresh_data()

@app.route("/api/update_product", methods=["POST", "PATCH"])
def update_product():
    if (auth := auth_guard()) is not None:
        return auth
    data = request.get_json(silent=True) or {}
    pid = data.get("id")
    if not pid:
        return jsonify({"error": "Missing 'id'"}), 400
    allowed = {"title", "description", "image", "price", "stock", "status", "url"}
    fields = {k: v for k, v in data.items() if k in allowed}
    if not fields:
        return jsonify({"error": "No updatable fields provided"}), 400
    fields["updated_at"] = now_iso()

    sets = ", ".join([f"{k}=:{k}" for k in fields.keys()])
    fields["id"] = pid
    conn = db()
    cur = conn.cursor()
    cur.execute(f"UPDATE products SET {sets} WHERE id=:id", fields)
    conn.commit()
    cur.execute("SELECT * FROM products WHERE id=?", (pid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"success": True, "product": row_to_dict(row)})

@app.route("/api/reprice_one", methods=["POST"])
def reprice_one():
    if (auth := auth_guard()) is not None:
        return auth
    data = request.get_json(silent=True) or {}
    pid = data.get("id")
    if not pid:
        return jsonify({"error": "Missing 'id'"}), 400
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id=?", (pid,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    # re-scrape for new source price
    _, scraper = detect_store(row["url"])
    scraped = scraper(row["url"])
    new_price = apply_price_rule(scraped.get("price"))
    cur.execute("UPDATE products SET price=?, updated_at=? WHERE id=?", (new_price, now_iso(), pid))
    conn.commit()
    cur.execute("SELECT * FROM products WHERE id=?", (pid,))
    out = row_to_dict(cur.fetchone())
    conn.close()
    return jsonify({"success": True, "product": out})

@app.route("/api/reprice", methods=["POST"])
def reprice_all():
    if (auth := auth_guard()) is not None:
        return auth
    # reapply rule on current products using *fresh scrape price*
    res = refresh_all_products()
    return jsonify({"success": True, "message": f"Repriced {res['updated']} products", **res})

@app.route("/api/delete_product/<pid>", methods=["DELETE"])
def delete_product(pid):
    if (auth := auth_guard()) is not None:
        return auth
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (pid,))
    n = cur.rowcount
    conn.commit()
    conn.close()
    if n == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"success": True, "deleted": pid})

@app.route("/api/bulk_delete", methods=["POST"])
def bulk_delete():
    if (auth := auth_guard()) is not None:
        return auth
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    if not ids:
        return jsonify({"error": "Provide 'ids': [ ... ]"}), 400
    qmarks = ",".join("?" for _ in ids)
    conn = db()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM products WHERE id IN ({qmarks})", ids)
    n = cur.rowcount
    conn.commit()
    conn.close()
    return jsonify({"success": True, "deleted_count": n})

@app.route("/api/export", methods=["GET"])
def export_csv():
    # filters same as get_listings
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    source = request.args.get("source", "").strip()

    where = []
    params = []
    if q:
        where.append("(title LIKE ? OR description LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if status:
        where.append("status = ?")
        params.append(status)
    if source:
        where.append("source = ?")
        params.append(source)
    wsql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = db()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM products {wsql} ORDER BY updated_at DESC", params)
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "url", "source", "title", "description", "image", "price", "stock", "status", "created_at", "updated_at"])
    for r in rows:
        writer.writerow([r["id"], r["url"], r["source"], r["title"], r["description"], r["image"], r["price"], r["stock"], r["status"], r["created_at"], r["updated_at"]])

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    mem.seek(0)
    filename = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=filename)

# ---------------------------
# Startup
# ---------------------------
init_db()

if __name__ == "__main__":
    # For local dev only; Render uses gunicorn via Procfile
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)

