import os
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

# Your eBay verification token
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"
ENDPOINT_URL = "https://my-dashboard-tqtg.onrender.com/ebay/verify"

@app.route("/ebay/verify", methods=["GET", "POST"])
def ebay_verify():
    if request.method == "GET":
        # Handle eBay challenge
        challenge_code = request.args.get("challenge_code")
        if not challenge_code:
            return jsonify({"error": "Missing challenge_code"}), 400

        m = hashlib.sha256()
        m.update(challenge_code.encode("utf-8"))
        m.update(VERIFICATION_TOKEN.encode("utf-8"))
        m.update(ENDPOINT_URL.encode("utf-8"))
        response_hash = m.hexdigest()

        return jsonify({"challengeResponse": response_hash}), 200

    elif request.method == "POST":
        # Handle actual eBay notifications
        try:
            payload = request.get_json(force=True)
            print("📩 Received eBay Notification:", payload)
            return "", 200
        except Exception as e:
            print("❌ Error processing eBay notification:", e)
            return "Internal Server Error", 500


@app.route("/")
def home():
    return jsonify({"message": "Dashboard API is running"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

