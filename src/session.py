from datetime import datetime, timezone, timedelta

import jwt
from flask import request

from src.config import config
from src.errors import InvalidSessionCode, NoSessionCode

SECRET_KEY = config("SECRET_KEY", None)


def create_session(user_id: object) -> object:
    current_time = datetime.now(tz=timezone.utc)
    session_duration = timedelta(minutes=60)
    session_code = jwt.encode({"user_id": str(user_id), "exp": current_time + session_duration}, SECRET_KEY)
    return session_code


def verify_session(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms="HS256")
        user_id = payload.get('user_id')
        return user_id
    except Exception as e:
        print("Invalid jwt token: " + str(e))
        raise InvalidSessionCode




def authenticate_user():
    session_code = request.headers.get("Authorization")
    if not session_code:
        raise NoSessionCode
    user_id = verify_session(session_code)
    return user_id
