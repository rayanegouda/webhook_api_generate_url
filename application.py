import os
import requests
from flask import Flask, request, jsonify
from cachetools import TTLCache

app = Flask(__name__)
GUAC_URL = os.getenv("GUACAMOLE_BASE_URL", "http://machines.vmascourse.com/guacamole")
GUAC_AUTH = f"{GUAC_URL}/api/tokens"
GUAC_CONNECTIONS = f"{GUAC_URL}/api/session/data/mysql/connections/"

USERNAME = os.getenv("GUACAMOLE_USERNAME")
PASSWORD = os.getenv("GUACAMOLE_PASSWORD")
token_cache = TTLCache(maxsize=1, ttl=300)

def get_token():
    if "token" in token_cache:
        return token_cache["token"]
    res = requests.post(GUAC_AUTH, data={"username": USERNAME, "password": PASSWORD})
    res.raise_for_status()
    token = res.json().get("authToken")
    token_cache["token"] = token
    return token

@app.route("/generate-url", methods=["POST"])
def generate_url():
    token = get_token()
    headers = {"Guacamole-Token": token}
    res = requests.get(GUAC_CONNECTIONS, headers=headers)
    res.raise_for_status()
    data = res.json()
    
    # Match by connection name or just get the first one
    connection_name = request.json.get("connection_name", "")
    conn_id = None
    for key, val in data.items():
        if val.get("name") == connection_name:
            conn_id = key
            break
    
    if not conn_id:
        return jsonify({"error": "Connection name not found"}), 404
    
    url = f"{GUAC_URL}/#/client/{conn_id}?token={token}"
    return jsonify({"guacamole_url": url})

if __name__ == "__main__":
    app.run()
