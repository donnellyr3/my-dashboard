from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests, time, os

app = Flask(__name__)

# 🔑 ScrapeOps API Key (use the one in Render’s Environment Variables)
SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY", "demo-key")

# ---------------------------
# 🧠 SCRAPER ROUTE
# ---------------------------
@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json(force=True)
    product_url = data.get("url")

    if not product_url:
        return jsonify({"success": False, "error": "Missing URL"}), 400

    proxy_url = "https://proxy.scrapeops.io/v1/"
    headers_url = "https://headers.scrapeops.io/v1/browser-headers"

    proxy_params = {
        "api_key": SCRAPEOPS_API_KEY,
        "url": product_url,
        "country": "us"
    }

    for attempt in range(3):
        try:
            h_res = requests.get(headers_url, params={"api_key": SCRAPEOPS_API_KEY, "num_results": "1"})
            browser_headers = h_res.json().get("result", [{}])[0]

            resp = requests.get(proxy_url, params=proxy_params, headers=browser_headers, timeout=30)
            html = resp.text

            soup = BeautifulSoup(html, "html.parser")
            title = soup.find("h1")
            price = (
                soup.find("span", {"class": "price-characteristic"}) or
                soup.find("span", {"class": "w_iUH7"}) or
                soup.find("span", {"class": "price"})
            )

            return jsonify({
                "success": True,
                "url": product_url,
                "title": title.text.strip() if title else "N/A",
                "price": price.text.strip() if price else "N/A"
            })
        except Exception as e:
            error_msg = str(e)
            time.sleep(2)
            continue

    return jsonify({
        "success": False,
        "error": f"Failed after 3 attempts: {error_msg}",
        "url": product_url
    }), 500


# ---------------------------
# 📦 INVENTORY ROUTE
# ---------------------------
@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify([
        {"id": 1, "title": "Demo Item 1", "price": 12.99, "stock": "In Stock"},
        {"id": 2, "title": "Demo Item 2", "price": 7.50, "stock": "Out of Stock"}
    ])


# ---------------------------
# 🏠 HOME ROUTE
# ---------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ Flask backend is LIVE on Render"


# ---------------------------
# 🚀 RUN APP
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

