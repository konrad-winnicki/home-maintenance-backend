class Error(Exception):
    pass


class DatabaseError(Error):
    pass


class ProductAlreadyExists(Error):
    pass


class NoSessionCode(Exception):
    pass


class InvalidSessionCode(Exception):
    pass
