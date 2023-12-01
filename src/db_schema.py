from db import create_table
from persistence import find_tables_in_database


def create_tables():
    existing_tables = find_tables_in_database(table_schema='public')
    print(existing_tables)
    if 'users' not in existing_tables:
        create_table(
            """ CREATE TABLE users (user_id VARCHAR(36) PRIMARY KEY, user_account_number VARCHAR(21) UNIQUE) """)
    if 'products' not in existing_tables:
        create_table(""" CREATE TABLE products (product_id VARCHAR(36) PRIMARY KEY, name VARCHAR(500) UNIQUE, user_id VARCHAR(36),
        CONSTRAINT fk_products_userId FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE) """)
    if 'store_positions' not in existing_tables:
        create_table(""" CREATE TABLE store_positions (product_id VARCHAR(36) PRIMARY KEY, quantity INTEGER, user_id VARCHAR(36), 
        CONSTRAINT fk_store_productId FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE, 
        CONSTRAINT fk_store_userId FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE)
        """)
    if 'barcodes' not in existing_tables:
        create_table(""" CREATE TABLE barcodes (product_id VARCHAR(36), barcode VARCHAR(13) PRIMARY KEY,
        CONSTRAINT fk_b FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE)""")
