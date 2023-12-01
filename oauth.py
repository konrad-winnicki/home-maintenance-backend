import json

import jwt
import requests
from decouple import config
from flask import request, redirect
from oauthlib.oauth2 import WebApplicationClient

from api import get_user_from_users, insert_user_to_users
from session import create_session

GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(GOOGLE_CLIENT_ID)


def registerOauthCallback(app):
    app.route("/code/callback")(callback)

def callback():
    response = get_token()
    id_token = response['id_token']
    decoded_token = jwt.decode(id_token, options={"verify_signature": False})
    user_account_number = decoded_token['sub']
    print("user account", user_account_number)
    if user_account_number != "denied":
        print("LOGGED")
        user_id = get_user_from_users(user_account_number)
        if not user_id:
            user_id = insert_user_to_users(user_account_number)
        session_code = create_session(user_id)
        return redirect('http://localhost:3000?session_code=' + session_code)



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
        redirect_url=request.base_url

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

