# Shinraa
# Ultra Lua Protector

Ultra Lua Protector is an **aggressive, environment-aware Lua protection system** designed to make your scripts **unusable in browsers, converters, and fake runtimes**, while remaining fully functional in **real exploit executors**.

### Features
- Executor-only environment validation
- Anti-browser, anti-converter, anti-sandbox
- Remote payload delivery
- Loader-based architecture
- Ready for Koyeb deployment

### API Endpoints

#### `POST /protect`
Upload a raw Lua script.  
Returns a **loader** that:
- Validates executor environment
- Fetches the protected payload
- Executes it securely

#### `GET /payload/<id>`
Returns the stored script.

### Deployment
Deploy directly to **Koyeb** using:
- `app.py`
- `requirements.txt`
- `Procfile`

### Warning
If the script is executed outside a real executor, it will **break aggressively**.
