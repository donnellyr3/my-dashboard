import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ Replace this with your real eBay verification token
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"

@app.route("/")
def home():
    return jsonify({"message": "Dashboard API is running"}), 200

@app.route("/ebay/verify", methods=["GET"])
def verify_ebay():
    challenge_code = request.args.get("challenge_code")
    if not challenge_code:
        return jsonify({"error": "Missing challenge_code"}), 400
    # eBay expects you to return your verification token
    return VERIFICATION_TOKEN, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

