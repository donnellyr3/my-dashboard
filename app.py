from flask import Flask, jsonify
import os, sys, time, socket

app = Flask(__name__)

# --- Basic routes ---
@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "🚀 11/10 Render-proof Flask app running perfectly"
    })

@app.route("/healthz")
@app.route("/render-ready")
def healthz():
    return jsonify({"status": "ok", "uptime": time.time()})

@app.route("/inventory")
def inventory():
    return jsonify([
        {"id": 1, "name": "Render-Proof Keyboard", "price": 25.99, "stock": "In Stock"},
        {"id": 2, "name": "Indestructible Mouse", "price": 14.50, "stock": "In Stock"}
    ])

def wait_for_port(port, retries=5):
    """Wait until the port is free (Render startup timing fix)."""
    for attempt in range(retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
            print(f"✅ Port {port} is ready (attempt {attempt+1})", flush=True)
            return True
        except OSError:
            print(f"⏳ Waiting for port {port}... (attempt {attempt+1})", flush=True)
            time.sleep(1)
    print(f"⚠️ Port {port} may already be in use, continuing anyway.", flush=True)
    return False

# --- Main entry ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("🧠 Booting 11/10 Flask build...", flush=True)
    time.sleep(1)
    wait_for_port(port)
    print(f"🚀 Launching Flask on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port)

