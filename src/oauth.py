import json

import jwt
import requests
from flask import request, jsonify
from oauthlib.oauth2 import WebApplicationClient

from src.config import config
from src.persistence import get_user_id, insert_user
from src.services import generate_unique_id
from src.session import create_session

GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(GOOGLE_CLIENT_ID)
FRONTEND_REDIRECT_URI = "http://localhost:3000/login"


def oauth2_code_callback():
    response = get_token()
    id_token = response['id_token']
    decoded_token = jwt.decode(id_token, options={"verify_signature": False})
    user_account_number = decoded_token['sub']
    user_email = (decoded_token['email'])
    if user_account_number != "denied":
        user_id = get_user_id(user_account_number)
        if not user_id:
            user_id = generate_unique_id()
            insert_user(user_id, user_account_number, user_email)
        session_code = create_session(user_id)
        return jsonify({"token": session_code}), 200


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


def get_token():
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    print("request url in get token:", request.url)
    print("redirect url in get token: ", request.base_url)
    auth_code_google_redirect = FRONTEND_REDIRECT_URI + "?" + request.query_string.decode();
    print("auth_code_google_redirect: ", auth_code_google_redirect)
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        # http is changed to https to prevent bug in the oauth library which enforces https event for localhost
        authorization_response=auth_code_google_redirect.replace("http", "https"),
        redirect_url=FRONTEND_REDIRECT_URI
    )

    print("GetTokenRequest Url:", token_url)
    print("GetTokenRequest Headers:", headers)
    print("GetTokenRequest Body:", body)
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    return client.parse_request_body_response(json.dumps(token_response.json()))
