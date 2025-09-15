from flask import Flask, jsonify, request
import threading, time

app = Flask(__name__)

# in-memory status dictionary
status = {
    "is_minor": False,
    "age_estimate": None,
    "last_seen": None
}

@app.route("/status", methods=["GET"])
def get_status():
    return jsonify(status)

@app.route("/update", methods=["POST"])
def update_status():
    data = request.get_json(force=True)
    # expected keys: is_minor (bool), age_estimate (int/str), last_seen (optional)
    status.update({
        "is_minor": data.get("is_minor", status["is_minor"]),
        "age_estimate": data.get("age_estimate", status["age_estimate"]),
        "last_seen": data.get("last_seen", time.strftime("%Y-%m-%d %H:%M:%S"))
    })
    return jsonify({"ok": True, "status": status})

def run():
    # for demo purposes, run on localhost:5001
    app.run(host="127.0.0.1", port=5001)

if __name__ == "__main__":
    run()