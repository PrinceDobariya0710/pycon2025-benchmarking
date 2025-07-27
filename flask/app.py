import os
from flask import Flask, request, jsonify, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric, Text
from dotenv import load_dotenv
import ujson

# Load environment variables from .env if present
load_dotenv()

# === ENVIRONMENT VARIABLES ===
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# === FLASK APP SETUP ===
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# === SQLALCHEMY MODEL ===
class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String)
    description = db.Column(Text)
    brand = db.Column(db.String)
    category = db.Column(db.String)
    price = db.Column(Numeric)
    currency = db.Column(db.String)
    stock = db.Column(db.Integer)
    ean = db.Column(db.String)
    color = db.Column(db.String)
    size = db.Column(db.String)
    availability = db.Column(db.String)
    internal_id = db.Column(db.String)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "brand": self.brand,
            "category": self.category,
            "price": float(self.price) if self.price is not None else None,
            "currency": self.currency,
            "stock": self.stock,
            "ean": self.ean,
            "color": self.color,
            "size": self.size,
            "availability": self.availability,
            "internal_id": self.internal_id,
        }


# === ROUTES ===
@app.route("/plain-text", methods=["GET"])
def plain_text():
    return ("Hello, world!", 200, {"Content-Type": "text/plain"})


@app.route("/json", methods=["GET"])
def json_serialization():
    return app.response_class(
        ujson.dumps({"message": "Hello, world from JSON serialization endpoint!"}),
        mimetype="application/json",
    )


@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json()
    product = Product(**data)
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@app.route("/products/<int:id>", methods=["GET"])
def get_product(id):
    product = db.session.get(Product, id)
    if not product:
        abort(404, description="Product not found")
    return jsonify(product.to_dict())


@app.route("/products", methods=["GET"])
def list_products():
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    products = Product.query.offset(offset).limit(limit).all()
    return jsonify([p.to_dict() for p in products])


@app.route("/products/<int:id>", methods=["PUT"])
def update_product(id):
    product = db.session.get(Product, id)
    if not product:
        abort(404, description="Product not found")
    data = request.get_json()
    for field, value in data.items():
        if hasattr(product, field):
            setattr(product, field, value)
    db.session.commit()
    return jsonify(product.to_dict())


@app.route("/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    product = db.session.get(Product, id)
    if not product:
        abort(404, description="Product not found")
    db.session.delete(product)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/fortune", methods=["GET"])
def fortune_100():
    products = Product.query.limit(100).all()
    return render_template("fortune.html", products=products)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
