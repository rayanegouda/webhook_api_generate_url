from flask import Flask, request, jsonify
import requests
import boto3
import os
from botocore.config import Config

app = Flask(__name__)

# Guacamole URL
GUAC_URL = "https://machines.vmascourse.com/guacamole"

# DynamoDB Config
aws_config = Config(
    max_pool_connections=100,
    retries={'max_attempts': 3}
)


aws_region_name = os.environ.get("AWS_REGION_NAME")
dynamodb = boto3.resource('dynamodb', region_name=aws_region_name, config=aws_config)
table_name = os.getenv("DYNAMODB_TABLE", "guacamole_users")
table = dynamodb.Table(table_name)

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
        dynamo_response = table.get_item(Key={"username": username})
        item = dynamo_response.get("Item")
        if not item:
            return jsonify({"error": "Username not found in DynamoDB"}), 404

        password = item.get("password")
        if not password:
            return jsonify({"error": "Password missing in DynamoDB"}), 500

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
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
