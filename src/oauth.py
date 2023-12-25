import json

import jwt
import requests
from flask import request, redirect, make_response
from oauthlib.oauth2 import WebApplicationClient

from src.config import config
from src.persistence import get_user_id, insert_user
from src.services import generate_unique_id
from src.session import create_session

GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(GOOGLE_CLIENT_ID)
FRONTENT_REDIRECT_URI = 'http://home-maintenace:3000'
# FRONTENT_REDIRECT_URI = 'http://localhost:3000'


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

        response = make_response(redirect('http://localhost:3000/'))
        # TODO: probably must be replace with passing by URL param
        response.set_cookie('session_code', session_code, domain="localhost") # TODO: how about domain???

        return response



def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


def get_token():
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    print("request url in get token:", request.url)
    print("redirect url in get token: ", request.base_url)
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url.replace("http", "https"),
        redirect_url=request.base_url # TODO: https must be forced on prod

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


def get_user_info():
    google_provider_cfg = get_google_provider_cfg()
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    print('user info', headers)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        return unique_id
    else:
        return "denied"

