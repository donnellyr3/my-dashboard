import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

# Flask setup
app = Flask(__name__)

# Database setup
db_path = os.path.join(os.path.dirname(__file__), "products.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "price": self.price, "stock": self.stock}

# Initialize database
with app.app_context():
    db.create_all()

# Routes
@app.route("/api/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    if not data.get("name") or data.get("price") is None:
        return jsonify({"error": "Name and price are required"}), 400
    product = Product(name=data["name"], price=data["price"], stock=data.get("stock", 0))
    db.session.add(product)
    db.session.commit()
    return jsonify({"message": "Product added", "product": product.to_dict()}), 201

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@app.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    if "name" in data:
        product.name = data["name"]
    if "price" in data:
        product.price = data["price"]
    if "stock" in data:
        product.stock = data["stock"]
    db.session.commit()
    return jsonify({"message": "Product updated", "product": product.to_dict()})

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"})

# Health check
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"message": "Dashboard API is running"}), 200

# Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

