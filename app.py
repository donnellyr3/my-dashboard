kfrom flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# Get ScrapeOps API key from Render environment variables
SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")

@app.route('/')
def home():
    return jsonify({"message": "✅ Scraper Worker is running!"})

@app.route('/test')
def test():
    """Quick test to verify ScrapeOps proxy connection"""
    try:
        test_url = "https://httpbin.org/ip"
        proxy_url = "https://proxy.scrapeops.io/v1/"
        proxy_params = {
            'api_key': SCRAPEOPS_API_KEY,
            'url': test_url
        }
        resp = requests.get(proxy_url, params=proxy_params, timeout=20)
        return jsonify({
            "success": True,
            "proxy_ip": resp.json(),
            "note": "✅ ScrapeOps proxy is working correctly!"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"success": False, "error": "Missing URL"}), 400

    try:
        # Step 1: Get realistic browser headers from ScrapeOps
        headers_resp = requests.get(
            'https://headers.scrapeops.io/v1/browser-headers',
            params={'api_key': SCRAPEOPS_API_KEY, 'num_results': '1'}
        )
        headers_resp.raise_for_status()
        browser_headers = headers_resp.json()['result'][0]

        # Step 2: Add realistic browsing metadata
        browser_headers['Referer'] = "https://www.google.com/"
        browser_headers['Accept-Language'] = "en-US,en;q=0.9"
        browser_headers['Accept-Encoding'] = "gzip, deflate, br"
        browser_headers['Accept'] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"

        # Step 3: Use ScrapeOps Proxy to avoid blocks
        proxy_url = "https://proxy.scrapeops.io/v1/"
        proxy_params = {
            'api_key': SCRAPEOPS_API_KEY,
            'url': url
        }

        resp = requests.get(proxy_url, params=proxy_params, headers=browser_headers, timeout=30)
        html = resp.text

        # Step 4: Parse title and price
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('h1')
        price = (
            soup.find('span', {'class': 'price-characteristic'}) or
            soup.find('span', {'class': 'w_iUH7'}) or
            soup.find('span', {'class': 'price'})
        )

        return jsonify({
            "success": True,
            "url": url,
            "title": title.text.strip() if title else "N/A",
            "price": price.text.strip() if price else "N/A"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

