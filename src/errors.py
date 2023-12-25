import socketio
from flask import jsonify


class Error(Exception):
    pass


class DatabaseError(Error):
    pass

class SocketHandShakeError(Error):
    pass

class ResourceAlreadyExists(Error):
    pass

class ResourceNotExists(Error):
    pass


class NoSessionCode(Exception):
    pass


class InvalidSessionCode(Exception):
    pass



def error_handler(exception):
    if isinstance(exception, (InvalidSessionCode, NoSessionCode)):
        print(exception)
        return jsonify({"response": "non-authorized"}), 401
    elif isinstance(exception, ResourceAlreadyExists):
        print(exception)
        return jsonify({"response": "resource already exists"}), 409
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
