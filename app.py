from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

# --- Optional: small delay to help Render detect readiness ---
time.sleep(1)

# --- Health Check Routes ---
@app.get("/healthz")
def healthz():
    """Render health check route."""
    return jsonify(status="ok")

@app.get("/")
def home():
    """Base route confirming backend is live."""
    return jsonify(status="ok", message="✅ Flask on Render (gunicorn) is live")

# --- Inventory Route (Mock Data) ---
@app.get("/inventory")
def inventory():
    """
    Returns mock inventory data for frontend testing.
    Later this will connect to eBay or ScrapeOps.
    """
    mock_data = [
        {"id": 1, "title": "Demo Item 1", "price": 12.99, "stock": "In Stock"},
        {"id": 2, "title": "Demo Item 2", "price": 7.50, "stock": "Out of Stock"},
        {"id": 3, "title": "Demo Item 3", "price": 19.99, "stock": "In Stock"}
    ]
    return jsonify(mock_data)

# --- Entry Point ---
if __name__ == "__main__":
    # This block only runs locally, not on Render
    app.run(host="0.0.0.0", port=5000, debug=True)

