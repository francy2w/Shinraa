from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets, hashlib, os

# =========================
# SHINRA CONFIG
# =========================

SYSTEM_NAME = "SHINRA"
EXECUTOR_HEADER = "X-ELLIS-CLIENT"
EXECUTOR_TOKEN  = "adolla-core"
BLOCKED_UA = ["Mozilla", "Chrome", "Safari", "Firefox", "Edge", "Opera"]

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# =========================
# DATABASE
# =========================

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True)
    expires = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)

# =========================
# UTILS
# =========================

def sha(x):
    return hashlib.sha256(x.encode()).hexdigest()

def new_key():
    return secrets.token_hex(32)

def is_browser():
    ua = request.headers.get("User-Agent", "")
    return any(b in ua for b in BLOCKED_UA)

def executor_ok():
    return request.headers.get(EXECUTOR_HEADER) == EXECUTOR_TOKEN

def license_ok(k):
    lic = License.query.filter_by(key=k, active=True).first()
    if not lic:
        return False
    if lic.expires < datetime.utcnow():
        lic.active = False
        db.session.commit()
        return False
    return True

# =========================
# GLOBAL GATE (ELLIS STYLE)
# =========================

@app.before_request
def gate():
    if is_browser() and not executor_ok():
        abort(403)

# =========================
# HANDSHAKE (ELLIS)
# =========================

@app.route("/api/handshake", methods=["POST"])
def handshake():
    if not executor_ok():
        return jsonify({"status": "blocked"}), 403

    return jsonify({
        "system": SYSTEM_NAME,
        "state": "ADOLLA_LINKED",
        "challenge": sha("shinra")
    })

# =========================
# AUTH
# =========================

@app.route("/api/auth", methods=["POST"])
def auth():
    if not executor_ok():
        return jsonify({"status": "executor_required"}), 403

    data = request.json
    key = data.get("key")

    if not license_ok(key):
        return jsonify({"status": "invalid_key"}), 403

    return jsonify({
        "status": "ok",
        "load": "/api/load/core.lua"
    })

# =========================
# SCRIPT DELIVERY
# =========================

@app.route("/api/load/<script>")
def load(script):
    key = request.args.get("key")

    if not executor_ok() or not license_ok(key):
        return "SHINRA BLOCKED", 403

    path = f"scripts/{script}"
    if not os.path.exists(path):
        return "404", 404

    return open(path, encoding="utf-8").read()

# =========================
# TEMP KEY GEN
# =========================

@app.route("/api/gen")
def gen():
    k = new_key()
    db.session.add(License(
        key=k,
        expires=datetime.utcnow() + timedelta(days=30)
    ))
    db.session.commit()
    return jsonify({"key": k})

# =========================
# INIT
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
