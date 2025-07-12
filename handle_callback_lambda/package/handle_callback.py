
import json
import base64
import requests
import jwt

def lambda_handler(event, context):
    # 1. Extract 'code' from query string
    query = event.get("queryStringParameters") or {}
    code = query.get("code")

    if not code:
        return {"statusCode": 400, "body": "Missing code"}

    # 2. Prepare token request
    client_id = "3rjl3gh2urarm3hqrlfi9vthmq"
    client_secret = "o4p2ptn5m1inr7223g4iah8h44our75aiflcg26fkn5d5pvljt1"
    redirect_uri = "https://staging.d37tilv61lh248.amplifyapp.com/callback.html"
    token_url = "https://autotrack-auth-001.auth.eu-north-1.amazoncognito.com/oauth2/token"

    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic_auth}"
    }

    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "redirect_uri": redirect_uri
    }

    # 3. Send POST request to get tokens
    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code != 200:
        return {"statusCode": 500, "body": f"Failed to fetch tokens: {response.text}"}

    tokens = response.json()
    id_token = tokens.get("id_token")

    # 4. Decode the ID token to extract user ID
    decoded = jwt.decode(id_token, options={"verify_signature": False})
    user_id = decoded.get("sub")
    email = decoded.get("email")

    # 5. Return user_id as JSON
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"user_id": user_id, "email": email})
    }
