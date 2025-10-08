import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory data storage (resets on server restart)
products = []
logs = []

# Health check endpoint for Render
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Dashboard API is running"}), 200

# Get all products
@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products), 200

# Add a new product
@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    if not data or "name" not in data:
        return jsonify({"error": "Product must have a name"}), 400
    products.append(data)
    logs.append(f"Added product: {data.get('name')}")
    return jsonify({"message": "Product added"}), 201

# Get logs
@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(logs), 200

# Optional: Root endpoint to test server
@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "running"}), 200

if __name__ == "__main__":
    # Use PORT environment variable for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

