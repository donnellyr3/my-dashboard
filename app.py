kfrom flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

# --- Health check route ---
@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "Scraper worker is running successfully"
    }), 200


# --- Example: Run your scraper manually ---
@app.route('/run-scraper', methods=['POST'])
def run_scraper():
    """
    Trigger your scraping script manually or from ScraperOps.
    Example: POST https://your-app.onrender.com/run-scraper
    """
    try:
        # Call your Python scraper file, e.g., walmart_scraper.py
        result = subprocess.run(
            ["python3", "walmart_scraper.py"],
            capture_output=True, text=True, check=True
        )
        return jsonify({
            "status": "success",
            "output": result.stdout
        }), 200
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "error": e.stderr
        }), 500


# --- Example: Update eBay listings ---
@app.route('/update-products', methods=['POST'])
def update_products():
    """
    Run your sync script to update eBay prices/inventory.
    """
    try:
        result = subprocess.run(
            ["python3", "update_products.py"],
            capture_output=True, text=True, check=True
        )
        return jsonify({
            "status": "success",
            "output": result.stdout
        }), 200
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "error": e.stderr
        }), 500


# --- Run the app (for Render) ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render assigns PORT dynamically
    app.run(host='0.0.0.0', port=port)

