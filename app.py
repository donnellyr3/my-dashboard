from flask import Flask, request, jsonify
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Scraper Worker is running"}), 200


@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"success": False, "error": "Missing 'url' in request"}), 400

    try:
        # Create a real browser-like scraper
        scraper = cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        })

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
                      "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }

        response = scraper.get(url, headers=headers)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Try to extract the title
        title = (
            soup.find("h1", {"class": "prod-ProductTitle"}) or
            soup.find("h1", {"itemprop": "name"}) or
            soup.find("title")
        )
        title_text = title.text.strip() if title else "N/A"

        # Try to extract price
        price = (
            soup.find("span", {"class": "price-characteristic"}) or
            soup.find("span", {"itemprop": "price"}) or
            soup.find("span", {"data-automation": "buybox-price"})
        )
        price_text = price.text.strip() if price else "N/A"

        # Return results
        return jsonify({
            "success": True,
            "url": url,
            "title": title_text,
            "price": price_text
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "url": url
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

