from flask import Flask, request

app = Flask(__name__)

# ✅ Your real eBay verification token goes here
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"

@app.route("/")
def home():
    return "Dashboard API is running", 200

@app.route("/ebay/verify", methods=["GET"])
def verify_ebay():
    challenge_code = request.args.get("challenge_code")
    if not challenge_code:
        return "Missing challenge_code", 400
    return VERIFICATION_TOKEN, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

