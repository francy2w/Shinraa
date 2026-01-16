import os
import uuid
from flask import Flask, request, send_file, jsonify, abort, make_response

app = Flask(__name__)

# Directory to store protected scripts
SCRIPT_DIR = "scripts"
os.makedirs(SCRIPT_DIR, exist_ok=True)

# Maximum script size (1 MB)
MAX_SCRIPT_SIZE = 1_000_000

# Security headers
@app.after_request
def apply_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store"
    return response

# Global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": "Internal server error"}), 500

@app.route("/", methods=["GET"])
def home():
    return {
        "status": "Ultra Lua Protector API",
        "message": "Executor-only environment validation active."
    }

@app.route("/protect", methods=["POST"])
def protect():
    # Reject missing content-type
    if not request.content_type:
        return jsonify({"error": "Missing Content-Type"}), 400

    # Reject non-text payloads
    if "text" not in request.content_type:
        return jsonify({"error": "Invalid Content-Type"}), 400

    # Reject empty body
    raw = request.data
    if not raw:
        return jsonify({"error": "Empty request body"}), 400

    # Reject oversized scripts
    if len(raw) > MAX_SCRIPT_SIZE:
        return jsonify({"error": "Script too large"}), 413

    # Decode safely
    try:
        script = raw.decode("utf-8", errors="ignore")
    except:
        return jsonify({"error": "Invalid UTF-8 encoding"}), 400

    if script.strip() == "":
        return jsonify({"error": "Script is empty"}), 400

    # Generate script ID
    script_id = str(uuid.uuid4())
    script_path = os.path.join(SCRIPT_DIR, f"{script_id}.lua")

    # Write script safely
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    loader = generate_loader(script_id)
    response = make_response(loader)
    response.headers["Content-Type"] = "text/plain"
    return response

@app.route("/payload/<script_id>", methods=["GET"])
def payload(script_id):
    # Reject invalid UUIDs
    try:
        uuid.UUID(script_id)
    except:
        return "-- invalid payload id", 404

    script_path = os.path.join(SCRIPT_DIR, f"{script_id}.lua")

    if not os.path.exists(script_path):
        return "-- invalid payload id", 404

    return send_file(script_path, mimetype="text/plain")

def generate_loader(script_id):
    return f"""
-- Ultra Lua Protector Loader (Shinraa Edition)
-- Extreme environment validation

local function is_executor()
    -- Basic executor fingerprints
    if getgenv or syn or identifyexecutor or is_synapse_function then
        return true
    end

    -- Deep exploit API checks
    if hookfunction or getrawmetatable or setreadonly or getrenv then
        return true
    end

    -- Roblox environment check
    if game and typeof(game) == "Instance" then
        return true
    end

    return false
end

if not is_executor() then
    -- Aggressive failure
    while true do
        error("Ultra Lua Protector: Invalid execution environment")
    end
end

local http_request = (syn and syn.request)
    or (http and http.request)
    or request
    or http_request

if not http_request then
    error("Ultra Lua Protector: No HTTP request function available")
end

local url = "https://YOUR-KOYEB-APP-URL/payload/{script_id}"

local response = http_request({{
    Url = url,
    Method = "GET"
}})

if not response then
    error("Ultra Lua Protector: No response from server")
end

local body = response.Body or response.body
if not body or body == "" then
    error("Ultra Lua Protector: Empty payload")
end

local fn, err = loadstring(body)
if not fn then
    error("Ultra Lua Protector: Failed to load payload: " .. tostring(err))
end

return fn()
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
