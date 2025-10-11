from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

# Get your ScrapeOps API key from Render environment variables
SCRAPEOPS_KEY = os.environ.get("SCRAPEOPS_KEY")

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

    api_url = "https://proxy.scrapeops.io/v1/"
    params = {
        "api_key": SCRAPEOPS_KEY,
        "url": product_url,
        "country": "us"
    }

    # Retry up to 3 times if ScrapeOps fails (proxy timeout, etc.)
    for attempt in range(3):
        try:
            res = requests.get(api_url, params=params, timeout=15)
            html = res.text.lower()

            # Check if blocked or bad status
            if res.status_code != 200 or "blocked" in html or "captcha" in html:
                time.sleep(2)  # short delay
                continue

            # --- Basic parsing for title and price ---
            title = "N/A"
            price = "N/A"

            if "<title>" in html:
                title = html.split("<title>")[1].split("</title>")[0][:100]

            if "$" in html:
                price = "$" + html.split("$")[1].split("<")[0][:6]

            return jsonify({
                "success": True,
                "title": title.strip(),
                "price": price.strip(),
                "url": product_url
            })

        except Exception as e:
            error_msg = str(e)
            time.sleep(2)
            continue

    # If all retries failed
    return jsonify({
        "success": False,
        "error": f"Failed to scrape after 3 attempts: {error_msg}",
        "url": product_url
    }), 500


@app.route("/", methods=["GET"])
def home():
    return "🕷️ Scraper Worker is Live with ScrapeOps Proxy!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

