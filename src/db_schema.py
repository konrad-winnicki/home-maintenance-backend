from db import create_schema


def create_tables():
    create_schema(
        """CREATE TABLE IF NOT EXISTS users
(
    user_id             VARCHAR(36) PRIMARY KEY,
    user_account_number VARCHAR(21) UNIQUE
);
CREATE TABLE IF NOT EXISTS products
(
    product_id VARCHAR(36) PRIMARY KEY,
    name       VARCHAR(500) UNIQUE,
    user_id    VARCHAR(36),
    CONSTRAINT fk_products_userId FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS store_positions
(
    product_id VARCHAR(36) PRIMARY KEY,
    quantity   INTEGER,
    user_id    VARCHAR(36),
    CONSTRAINT fk_store_productId FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_store_userId FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS barcodes
(
    product_id VARCHAR(36),
    barcode    VARCHAR(13) PRIMARY KEY,
    CONSTRAINT fk_b FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE CASCADE ON UPDATE CASCADE
);
""")
