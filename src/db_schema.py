from db import create_schema


def create_tables():
    create_schema(
        """
CREATE TABLE IF NOT EXISTS users
(
    id                  UUID PRIMARY KEY,
    user_account_number VARCHAR(128) UNIQUE
);
CREATE TABLE IF NOT EXISTS products
(
    id         UUID PRIMARY KEY,
    name       VARCHAR(512) UNIQUE,
    user_id    UUID,
    quantity   INTEGER,
    CONSTRAINT fk_products_userId FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS shopping_list_items
(
    id UUID PRIMARY KEY,
    name       VARCHAR(512) UNIQUE,
    user_id    UUID,
    quantity   INTEGER,
    is_bought  BOOLEAN,
    CONSTRAINT fk_users_userId FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS barcodes
(
    id         UUID,
    barcode    VARCHAR(13) PRIMARY KEY
);
""")
