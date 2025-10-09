from flask import Flask, request

app = Flask(__name__)

VERIFICATION_TOKEN = "obSdraqjX9Y8gChpMnbymcxsm3coqckG"  # 👈 hardcoded token

@app.route("/ebay/verify", methods=["GET"])
def verify_ebay():
    challenge_code = request.args.get("challenge_code")
    return VERIFICATION_TOKEN, 200

