from flask import Flask, request

app = Flask(__name__)

# ✅ This is your actual verification token
VERIFICATION_TOKEN = "b4e29a1fd9c2461d8f3a2c7e8a90b123456789ab"

@app.route("/ebay/verify", methods=["GET"])
def verify_ebay():
    challenge_code = request.args.get("challenge_code")
    return VERIFICATION_TOKEN, 200

@app.route("/")
def home():
    return {"message": "Dashboard API is running"}

