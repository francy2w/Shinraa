from flask import Flask, request, jsonify, render_template, redirect, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import hashlib, secrets, os

# ================= CONFIG =================

APP_NAME = "SHINRA"
CLIENT_HEADER = "X-SHINRA-CLIENT"
CLIENT_TOKEN  = "adolla-burst"
BLOCKED_UA = ["Mozilla", "Chrome", "Safari", "Firefox", "Edge"]

app = Flask(__name__)
app.secret_key = "shinra-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ================= DATABASE =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(64))

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True)
    hwid = db.Column(db.String(64))
    ip = db.Column(db.String(32))
    expires = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)

# ================= UTILS =================

def sha(x): return hashlib.sha256(x.encode()).hexdigest()
def new_key(): return secrets.token_hex(32)

def is_browser():
    ua = request.headers.get("User-Agent", "")
    return any(b in ua for b in BLOCKED_UA)

def client_ok():
    return request.headers.get(CLIENT_HEADER) == CLIENT_TOKEN

def license_ok(k, hwid, ip):
    lic = License.query.filter_by(key=k, active=True).first()
    if not lic or lic.expires < datetime.utcnow():
        return False
    if lic.hwid and lic.hwid != hwid:
        return False
    if lic.ip and lic.ip != ip:
        return False
    lic.hwid = hwid
    lic.ip = ip
    db.session.commit()
    return True

# ================= GATE =================

@app.before_request
def gate():
    if is_browser() and not request.path.startswith("/dashboard") and not request.path.startswith("/login"):
        abort(403)

# ================= AUTH WEB =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = sha(request.form["password"])
        user = User.query.filter_by(username=u, password=p).first()
        if user:
            session["uid"] = user.id
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "uid" not in session:
        return redirect("/login")
    licenses = License.query.all()
    return render_template("dashboard.html", licenses=licenses, app=APP_NAME)

# ================= API (ELLIS STYLE) =================

@app.route("/api/handshake", methods=["POST"])
def handshake():
    if not client_ok():
        return jsonify({"status": "blocked"}), 403
    return jsonify({
        "system": APP_NAME,
        "state": "ADOLLA_LINKED",
        "time": datetime.utcnow().isoformat()
    })

@app.route("/api/auth", methods=["POST"])
def auth():
    if not client_ok():
        return jsonify({"status": "client_required"}), 403

    d = request.json
    if not license_ok(d["key"], d["hwid"], request.remote_addr):
        return jsonify({"status": "denied"}), 403

    return jsonify({
        "status": "ok",
        "payload": "/api/load/core"
    })

@app.route("/api/load/<name>")
def load(name):
    key = request.args.get("key")
    hwid = request.args.get("hwid")
    if not client_ok() or not license_ok(key, hwid, request.remote_addr):
        abort(403)
    return open(f"payloads/{name}.txt").read()

# ================= INIT =================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.first():
            db.session.add(User(username="admin", password=sha("admin")))
            db.session.add(
                License(
                    key=new_key(),
                    expires=datetime.utcnow() + timedelta(days=30)
                )
            )
            db.session.commit()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
