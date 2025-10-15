from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.get("/healthz")
def healthz():
    return jsonify(status="ok")

@app.get("/")
def home():
    return jsonify(status="ok", message="✅ Flask on Render (gunicorn) is live")

# no app.run() here; gunicorn will start the app

