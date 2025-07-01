from flask import Flask, request, jsonify
import requests
import os
import base64

app = Flask(__name__)

GUAC_BASE_URL = os.getenv("GUACAMOLE_BASE_URL", "http://machines.vmascourse.com/guacamole")
GUAC_USERNAME = os.getenv("GUACAMOLE_USERNAME", "guacadmin")
GUAC_PASSWORD = os.getenv("GUACAMOLE_PASSWORD", "guacadmin")
GUAC_TOKEN_URL = f"{GUAC_BASE_URL}/api/tokens"

def get_token():
    res = requests.post(
        GUAC_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"username": GUAC_USERNAME, "password": GUAC_PASSWORD}
    )
    res.raise_for_status()
    return res.json().get("authToken")

def generate_obfuscated_id(connection_id):
    raw = f"{connection_id}\tc\tmysql"
    encoded = base64.b64encode(raw.encode()).decode().replace("=", "")
    return encoded

@app.route("/generate-url", methods=["POST"])
def generate_url():
    try:
        data = request.get_json()
        connection_id = data.get("connection_id")
        if not connection_id:
            return jsonify({"error": "connection_id is required"}), 400

        token = get_token()
        client_id = generate_obfuscated_id(connection_id)
        final_url = f"{GUAC_BASE_URL}/#/client/{client_id}?token={token}"
        return jsonify({"guacamole_url": final_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, port=5000)
