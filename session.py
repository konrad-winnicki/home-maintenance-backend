from datetime import datetime, timezone, timedelta

import jwt
from decouple import config
from flask import request

SECRET_KEY = config("SECRET_KEY", None)


class NoSessionCode(Exception):
    pass


class InvalidSessionCode(Exception):
    pass


def create_session(user_id):
    current_time = datetime.now(tz=timezone.utc)
    session_duration = timedelta(minutes=1)
    session_code = jwt.encode({"user_id": user_id, "exp": current_time + session_duration}, SECRET_KEY)
    return session_code


def verify_session(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms="HS256")
        user_id = payload.get('user_id')
        return user_id
    except jwt.ExpiredSignatureError:
        raise InvalidSessionCode


def authenticate_user():
    session_code = request.headers.get("Authorization")
    if not session_code:
        raise NoSessionCode
    user_id = verify_session(session_code)
    return user_id
