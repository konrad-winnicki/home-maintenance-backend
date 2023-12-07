from db import create_schema

# TODO: make just 'id' in every table
def create_tables():
    create_schema(
        """CREATE TABLE IF NOT EXISTS users
(
    user_id             UUID PRIMARY KEY,
    user_account_number VARCHAR(128) UNIQUE
);
CREATE TABLE IF NOT EXISTS products
(
    product_id UUID PRIMARY KEY,
    name       VARCHAR(512) UNIQUE,
    user_id    UUID,
    quantity   INTEGER,
    CONSTRAINT fk_products_userId FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS shopping_list_items
(
    id UUID PRIMARY KEY,
    name       VARCHAR(512) UNIQUE,
    user_id    UUID,
    quantity   INTEGER,
    is_bought  BOOLEAN,
    CONSTRAINT fk_users_userId FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS barcodes
(
    product_id UUID,
    barcode    VARCHAR(13) PRIMARY KEY,
    CONSTRAINT fk_b FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE CASCADE ON UPDATE CASCADE
);
""")



