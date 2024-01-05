from flask import jsonify
from socketio.exceptions import SocketIOError


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

class DatabaseCheckViolation(Exception):
    def __init__(self, message):
        self.message = message
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
        return jsonify({"BadRequest": exception.message}), 400
    elif isinstance(exception, ResourceNotExists):
        print(exception)
        return jsonify({"response": "resource does not exist"}), 404
    elif isinstance(exception, DatabaseError):
        print(exception)
        return jsonify({"response": "database error"}), 500
    elif isinstance(exception, SocketHandShakeError):
        print('Invalid token during socket handshake')
    elif isinstance(exception, SocketIOError):
        print('Invalid token during socket handshake')
    elif isinstance(exception, DatabaseCheckViolation):
        if "quantity" in exception.message:
            return jsonify({"QuantityViolation": "quantity must be >= 0"}), 400
    elif isinstance(exception, Exception):
        print(exception)
        return "unknown error", 500
