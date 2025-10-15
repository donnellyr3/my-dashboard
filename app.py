kfrom flask import Flask, request, jsonify
import os
import requests
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

# 🔑 Get your ScrapeOps API key from Render environment variables
SCRAPEOPS_KEY = os.environ.get("SCRAPEOPS_KEY")

# ---------------------------
# 🕷️ SCRAPE ROUTE
# ---------------------------
@app.route("/scrape", methods=["POST"])
def scrape():
    """
    Scrapes a given product URL using the ScrapeOps proxy API
    and returns basic info like title and price.
    """
    data = request.get_json()
    product_url = data.get("url")

    if not product_url:
        return jsonify({"success": False, "error": "Missing URL"}), 400

    proxy_url = "https://proxy.scrapeops.io/v1/"
    headers_url = "https://headers.scrapeops.io/v1/browser-headers"
    proxy_params = {
        "api_key": SCRAPEOPS_KEY,
        "url": product_url,
        "country": "us"
    }

    # Try up to 3 times with randomized headers
    for attempt in range(3):
        try:
            # Get random browser headers
            h_res = requests.get(headers_url, params={"api_key": SCRAPEOPS_KEY, "num_results": "1"})
            browser_headers = h_res.json().get("result", [{}])[0]

            # Fetch the page
            resp = requests.get(proxy_url, params=proxy_params, headers=browser_headers, timeout=30)
            html = resp.text

            # Parse title and price
            soup = BeautifulSoup(html, "html.parser")
            title = soup.find("h1")
            price = (
                soup.find("span", {"class": "price-characteristic"}) or
                soup.find("span", {"class": "w_iUH7"}) or
                soup.find("span", {"class": "price"})
            )

            # Return parsed info
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

    # If all retries failed
    return jsonify({
        "success": False,
        "error": f"Failed after 3 attempts: {error_msg}",
        "url": product_url
    }), 500


# ---------------------------
# 📦 INVENTORY ROUTE (temporary mock data)
# ---------------------------
@app.route("/inventory", methods=["GET"])
def get_inventory():
    """
    Returns mock inventory data for testing until live sync is connected.
    """
    data = [
        {"title": "Demo Item 1", "price": 12.99, "stock": "In Stock", "id": 1},
        {"title": "Demo Item 2", "price": 7.50, "stock": "Out of Stock", "id": 2}
    ]
    return jsonify(data)


# ---------------------------
# 🏠 HOME ROUTE
# ---------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ Scraper Worker Live with Browser Headers"


# ---------------------------
# 🚀 RUN APP (only once)
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

