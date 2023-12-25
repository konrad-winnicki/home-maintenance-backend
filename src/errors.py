import socketio
from flask import jsonify


class Error(Exception):
    pass


class DatabaseError(Exception):
    pass

class SocketHandShakeError(Exception):
    pass

class ResourceAlreadyExists(Exception):
    pass

class ResourceNotExists(Exception):
    pass


class NoSessionCode(Exception):
    pass

class BadRequest(Exception):
    def __init__(self, expected_attributes):
        self.message = "Request should contain object {}".format(expected_attributes)
        super().__init__(self.message)
    pass


class InvalidSessionCode(Exception):
    pass



def error_handler(exception):
    print('aaaaaaaaaa', exception)

    if isinstance(exception, (InvalidSessionCode, NoSessionCode)):
        print(exception)
        return jsonify({"response": "non-authorized"}), 401
    elif isinstance(exception, ResourceAlreadyExists):
        print(exception)
        return jsonify({"response": "resource already exists"}), 409
    elif isinstance(exception, BadRequest):
        print(exception)
        return jsonify({"response": exception.message}), 400
    elif isinstance(exception, ResourceNotExists):
        print(exception)
        return jsonify({"response": "resource does not exist"}), 404
    elif isinstance(exception, DatabaseError):
        print(exception)
        return jsonify({"response": "database error"}), 500
    elif isinstance(exception, SocketHandShakeError):
        print('Invalid token during socket handshake')
    elif isinstance(exception, socketio.exceptions):
        print('Invalid token during socket handshake')
    elif isinstance(exception, Exception):
        print(exception)
        return "unknown error", 500
