from flask import Flask, request, jsonify
import requests
import boto3
import os
import logging
from botocore.config import Config

# Configuration logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Guacamole URL
GUAC_URL = "https://machines.vmascourse.com/guacamole"

# AWS config
aws_config = Config(
    max_pool_connections=100,
    retries={'max_attempts': 3}
)

# DynamoDB Setup
dynamodb = boto3.resource('dynamodb', region_name="eu-north-1")
table_name = os.getenv("DYNAMODB_TABLE", "guacamole_users")
table = dynamodb.Table(table_name)


def get_password_from_dynamodb(username):
    """
    Récupère le mot de passe associé à un username depuis la table DynamoDB 'guacamole_users'.
    Retourne None si l'utilisateur n'existe pas.
    """
    try:
        response = table.get_item(Key={"username": username})
        item = response.get("Item")
        if item and "password" in item:
            return item["password"]
        else:
            logging.warning(f"⚠️ Aucun utilisateur trouvé avec le username : {username}")
            return None
    except Exception as e:
        logging.error(f"❌ Erreur lors de la récupération du mot de passe : {str(e)}")
        return None


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Guacamole Token API is up"}), 200


@app.route("/api/final-login", methods=["POST"])
def final_login():
    try:
        data = request.get_json()
        username = data.get("username")
        connection_id = data.get("connection_id")

        if not all([username, connection_id]):
            return jsonify({"error": "Missing username or connection_id"}), 400

        # 🔍 Récupération du mot de passe dans DynamoDB
        password = get_password_from_dynamodb(username)
        if not password:
            return jsonify({"error": "User not found in DynamoDB"}), 404

        # 🔐 Authentification Guacamole
        response = requests.post(
            f"{GUAC_URL}/api/tokens",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"username={username}&password={password}"
        )
        response.raise_for_status()
        token = response.json().get("authToken")

        if not token:
            return jsonify({"error": "No token returned by Guacamole"}), 502

        return jsonify({
            "url": f"{GUAC_URL}/#/client/c/{connection_id}?token={token}"
        })

    except Exception as e:
        logging.error(f"❌ Exception dans /api/final-login : {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
