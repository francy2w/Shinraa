import os
import uuid
from flask import Flask, request, jsonify, send_file, abort

app = Flask(__name__)

# Directory to store protected scripts
SCRIPT_DIR = "scripts"
os.makedirs(SCRIPT_DIR, exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    return {
        "status": "Ultra Lua Protector API",
        "message": "Environment-aware, executor-only Lua protection system."
    }

@app.route("/protect", methods=["POST"])
def protect():
    script = request.data.decode("utf-8")

    if not script or script.strip() == "":
        return jsonify({"error": "No script provided"}), 400

    script_id = str(uuid.uuid4())
    script_path = os.path.join(SCRIPT_DIR, f"{script_id}.lua")

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    loader = generate_loader(script_id)

    return loader, 200, {"Content-Type": "text/plain"}

@app.route("/payload/<script_id>", methods=["GET"])
def payload(script_id):
    script_path = os.path.join(SCRIPT_DIR, f"{script_id}.lua")

    if not os.path.exists(script_path):
        return "-- invalid payload id", 404

    return send_file(script_path, mimetype="text/plain")

def generate_loader(script_id):
    return f"""
-- Ultra Lua Protector Loader
-- Aggressive environment validation

local function is_executor()
    if getgenv or syn or identifyexecutor or is_synapse_function then
        return true
    end

    if hookfunction or getrawmetatable or setreadonly then
        return true
    end

    return false
end

if not is_executor() then
    error("Ultra Lua Protector: Invalid execution environment")
end

local http_request = (syn and syn.request) or (http and http.request) or request or http_request
if not http_request then
    error("Ultra Lua Protector: No HTTP request function available")
end

local url = "https://YOUR-KOYEB-APP-URL/payload/{script_id}"

local response = http_request({
    Url = url,
    Method = "GET"
})

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
