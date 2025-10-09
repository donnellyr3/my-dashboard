import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ Your actual verification token (already approved)
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"

# ✅ Your exact endpoint URL, must match eBay settings
ENDPOINT_URL = "https://my-dashboard-tqtg.onrender.com/ebay/verify"


@app.route("/ebay/verify", methods=["GET"])
def ebay_verify():
    """
    Respond to eBay's challenge request for marketplace account deletion notifications.
    eBay will call this with ?challenge_code=XYZ
    We must hash challengeCode + verificationToken + endpoint (in that order),
    and return JSON with challengeResponse.
    """
    challenge_code = request.args.get("challenge_code")
    if not challenge_code:
        return jsonify({"error": "Missing challenge_code"}), 400

    # Concatenate challengeCode + verificationToken + endpoint
    data_to_hash = f"{challenge_code}{VERIFICATION_TOKEN}{ENDPOINT_URL}"

    # Compute SHA-256 hash
    hashed = hashlib.sha256(data_to_hash.encode("utf-8")).hexdigest()

    # Return the response in the exact format eBay expects
    return jsonify({"challengeResponse": hashed}), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Dashboard API is running"}), 200


if __name__ == "__main__":
    # Run locally for testing
    app.run(host="0.0.0.0", port=5000)

