from flask import Flask, request, jsonify
import requests
import os
from cachetools import TTLCache
import logging

app = Flask(__name__)

# Configuration via variables d'environnement
GUACAMOLE_BASE_URL = os.getenv("GUACAMOLE_BASE_URL", "http://machines.vmascourse.com/guacamole")
GUACAMOLE_USERNAME = os.getenv("GUACAMOLE_USERNAME")
GUACAMOLE_PASSWORD = os.getenv("GUACAMOLE_PASSWORD")
GUACAMOLE_API_URL = f"{GUACAMOLE_BASE_URL}/api/tokens"

# Cache pour le token (expire après 5 minutes)
token_cache = TTLCache(maxsize=1, ttl=300)

# Logging
logging.basicConfig(level=logging.INFO)

def get_guacamole_token():
    """Récupère le token Guacamole avec cache."""
    if "token" in token_cache:
        return token_cache["token"]

    try:
        auth_res = requests.post(
            GUACAMOLE_API_URL,
            data={"username": GUACAMOLE_USERNAME, "password": GUACAMOLE_PASSWORD},
            timeout=5
        )
        auth_res.raise_for_status()
        token = auth_res.json().get("authToken")
        if token:
            token_cache["token"] = token
            return token
    except requests.exceptions.RequestException as e:
        logging.error(f"Guacamole auth failed: {e}")
        raise

@app.route("/generate-url", methods=["POST"])
def generate_url():
    data = request.json
    connection_id = data.get("connection_id")

    if not connection_id or not isinstance(connection_id, str):
        return jsonify({"error": "connection_id must be a valid string"}), 400

    try:
        token = get_guacamole_token()
        access_url = f"{GUACAMOLE_BASE_URL}/#/client/{connection_id}?token={token}"
        return jsonify({"guacamole_url": access_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
