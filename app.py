import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# ✅ Simple in-memory storage (you can switch to a DB later)
products = []
logs = []

# 🏠 Home route
@app.route("/")
def home():
    return {"message": "Dashboard API is running"}, 200

# 📦 Products — Get all products
@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products)

# 📦 Products — Add product
@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    products.append(data)
    logs.append(f"Added product: {data.get('name')}")
    return jsonify({"message": "Product added"}), 201

# 📜 Logs — View simple logs
@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(logs)

# 🧠 eBay verification endpoint (for Marketplace Account

