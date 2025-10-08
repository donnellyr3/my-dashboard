import os
from flask import Flask, jsonify, request

app = Flask(__name__)

products = []
logs = []

@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products)

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    products.append(data)
    logs.append(f"Added product: {data.get('name')}")
    return jsonify({"message": "Product added"}), 201

@app.route("/api/products/bulk", methods=["POST"])
def add_products_bulk():
    data = request.json
    if not isinstance(data, list):
        return jsonify({"error": "Expected a list of products"}), 400
    for product in data:
        products.append(product)
        logs.append(f"Added product: {product.get('name')}")
    return jsonify({"message": f"{len(data)} products added"}), 201

@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(logs)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

