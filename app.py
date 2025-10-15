from flask import Flask, request, jsonify
import os
import requests
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

# 🔑 Environment variable for ScrapeOps API key
SCRAPEOPS_API_KEY = os.environ.get("SCRAPEOPS_KEY")

# ---------------------------
# 🕷️ SCRAPE ROUTE
# ---------------------------
@app.route("/scrape", methods=["POST"])
def scrape():
    """
    Scrapes a given product URL using ScrapeOps proxy and browser headers.
    Returns title and price.
    """
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"success": False, "error": "Missing URL"}), 400

    proxy_url = "https://proxy.scrapeops.io/v1/"
    headers_url = "https://headers.scrapeops.io/v1/browser-headers"

    # Try up to 3 times with random browser headers
    for attempt in range(3):
        try:
            # Step 1: Get random realistic browser headers
            headers_resp = requests.get(
                headers_url,
                params={"api_key": SCRAPEOPS_API_KEY, "num_results": "1"}
            )
            headers_resp.raise_for_status()
            browser_headers = headers_resp.json()["result"][0]

            # Step 2: Add browsing metadata
            browser_headers.update({
                "Referer": "https://www.google.com/",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            })

            # Step 3: Scrape via ScrapeOps Proxy
            proxy_params = {"api_key": SCRAPEOPS_API_KEY, "url": url, "country": "us"}
            resp = requests.get(proxy_url, params=proxy_params, headers=browser_headers, timeout=30)
            html = resp.text

            # Step 4: Parse title and price
            soup = BeautifulSoup(html, "html.parser")
            title = soup.find("h1")
            price = (
                soup.find("span", {"class": "price-characteristic"}) or
                soup.find("span", {"class": "w_iUH7"}) or
                soup.find("span", {"class": "price"})
            )

            return jsonify({
                "success": True,
                "url": url,
                "title": title.text.strip() if title else "N/A",
                "price": price.text.strip() if price else "N/A"
            })

        except Exception as e:
            error_msg = str(e)
            time.sleep(2)
            continue

    # If all retries fail
    return jsonify({
        "success": False,
        "error": f"Failed after 3 attempts: {error_msg}",
        "url": url
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

