import os
import requests
from flask import Flask, request, jsonify
from cachetools import TTLCache

app = Flask(__name__)

# Environnement
GUAC_BASE = os.getenv("GUACAMOLE_BASE_URL", "http://machines.vmascourse.com/guacamole")
GUAC_TOKEN_URL = f"{GUAC_BASE}/api/tokens"
GUAC_CONN_URL = f"{GUAC_BASE}/api/session/data/mysql/connections/"
GUAC_USER = os.getenv("GUACAMOLE_USERNAME")
GUAC_PASS = os.getenv("GUACAMOLE_PASSWORD")

# Cache token 5 min
token_cache = TTLCache(maxsize=1, ttl=300)

def get_token():
    if "token" in token_cache:
        return token_cache["token"]

    res = requests.post(GUAC_TOKEN_URL, data={"username": GUAC_USER, "password": GUAC_PASS})
    res.raise_for_status()
    token = res.json().get("authToken")
    if not token:
        raise Exception("Token missing in response.")
    token_cache["token"] = token
    return token

@app.route("/generate-url", methods=["POST"])
def generate_url():
    content = request.json
    connection_name = content.get("connection_name", "")
    if not connection_name:
        return jsonify({"error": "Missing connection_name"}), 400

    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(GUAC_CONN_URL, headers=headers)
    res.raise_for_status()

    connections = res.json()
    for conn_id, details in connections.items():
        if details.get("name") == connection_name:
            final_url = f"{GUAC_BASE}/#/client/{conn_id}?token={token}"
            return jsonify({"guacamole_url": final_url})

    return jsonify({"error": "Connection not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
