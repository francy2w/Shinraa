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

local response = http_request({{
    Url = url,
    Method = "GET"
}})

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
