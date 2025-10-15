from flask import Flask, jsonify
import os, time

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "🚀 Render-proof Flask app running perfectly"
    })

@app.route("/healthz")
def healthz():
    # Always return 200 so Render passes the health check
    return jsonify({
        "status": "ok",
        "uptime": time.time()
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Launching Flask app on port {port}", flush=True)
    time.sleep(1)  # short buffer for Render startup
    app.run(host="0.0.0.0", port=port)

