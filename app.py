from flask import Flask, request, jsonify
import requests
import os
import logging
from cachetools import TTLCache

app = Flask(__name__)

# Configuration
GUACAMOLE_BASE_URL = os.getenv("GUACAMOLE_BASE_URL", "http://machines.vmascourse.com/guacamole")
GUACAMOLE_USERNAME = os.getenv("GUACAMOLE_USERNAME")
GUACAMOLE_PASSWORD = os.getenv("GUACAMOLE_PASSWORD")
GUACAMOLE_API_URL = f"{GUACAMOLE_BASE_URL}/api/tokens"

# Cache du token (5 minutes)
token_cache = TTLCache(maxsize=1, ttl=300)

# Logging
logging.basicConfig(level=logging.INFO)

def get_guacamole_token():
    """Authentifie auprès de Guacamole et retourne un token, avec cache."""
    if "token" in token_cache:
        return token_cache["token"]

    try:
        response = requests.post(
            GUACAMOLE_API_URL,
            data={"username": GUACAMOLE_USERNAME, "password": GUACAMOLE_PASSWORD},
            timeout=5
        )
        response.raise_for_status()
        token = response.json().get("authToken")
        if token:
            token_cache["token"] = token
            return token
        raise ValueError("Token not found in response.")
    except Exception as e:
        logging.error(f"Erreur d'authentification Guacamole : {e}")
        raise

@app.route("/generate-url", methods=["POST"])
def generate_url():
    """Retourne une URL d'accès Guacamole à partir d'un ID de connexion."""
    data = request.get_json()
    connection_id = data.get("connection_id")

    if not connection_id:
        return jsonify({"error": "Le champ 'connection_id' est requis."}), 400

    try:
        token = get_guacamole_token()
        url = f"{GUACAMOLE_BASE_URL}/#/client/{connection_id}?token={token}"
        return jsonify({"guacamole_url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
