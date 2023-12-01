class Error(Exception):
    pass


class DatabaseError(Error):
    pass

class ProductAlreadyExists(Error):
    pass
