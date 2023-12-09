class Error(Exception):
    pass


class DatabaseError(Error):
    pass


class ResourceAlreadyExists(Error):
    pass

class ResourceNotExists(Error):
    pass


class NoSessionCode(Exception):
    pass


class InvalidSessionCode(Exception):
    pass
