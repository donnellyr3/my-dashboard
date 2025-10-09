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

