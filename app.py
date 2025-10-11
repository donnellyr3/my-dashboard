from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

SCRAPEOPS_KEY = os.environ.get("SCRAPEOPS_KEY")

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    product_url = data.get("url")

    if not product_url:
        return jsonify({"success": False, "error": "Missing URL"}), 400

    proxy_url = "https://proxy.scrapeops.io/v1/"
    headers_url = "https://headers.scrapeops.io/v1/browser-headers"
    params = {"api_key": SCRAPEOPS_KEY, "url": product_url, "country": "us"}

    # Retry 3 times with random browser headers
    for attempt in range(3):
        try:
            # ✅ get random real browser headers
            h_res = requests.get(headers_url, params={"api_key": SCRAPEOPS_KEY, "num_results": "1"})
            headers = h_res.json()["result"][0]

            res = requests.get(proxy_url, params=params, headers=headers, timeout=20)
            html = res.text.lower()

            if res.status_code != 200 or "robot" in html or "captcha" in html:
                time.sleep(2)
                continue

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

    return jsonify({
        "success": False,
        "error": f"Failed after 3 attempts: {error_msg}",
        "url": product_url
    }), 500


@app.route("/", methods=["GET"])
def home():
    return "✅ Scraper Worker Live with Browser Headers"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
