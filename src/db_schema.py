from db import create_schema


def create_tables():
    create_schema(
        """
CREATE TABLE IF NOT EXISTS users
(
    id                  UUID PRIMARY KEY,
    user_account_number VARCHAR(128) UNIQUE
);
CREATE TABLE IF NOT EXISTS homes 
(
    id                  UUID PRIMARY KEY,
    name                VARCHAR(128)
);
CREATE TABLE IF NOT EXISTS home_members
(
    home_id                 UUID,
    user_id                 UUID,
    PRIMARY KEY (home_id, user_id),
    CONSTRAINT fk_home_members_homeId FOREIGN KEY (home_id) REFERENCES homes (id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_home_members_userId FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS products
(
    id         UUID PRIMARY KEY,
    name       VARCHAR(512),
    home_id    UUID,
    quantity   INTEGER,
    CONSTRAINT products_unique_name UNIQUE (home_id, name),
    CONSTRAINT fk_products_home_id FOREIGN KEY (home_id) REFERENCES homes (id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS shopping_list_items
(
    id UUID PRIMARY KEY,
    name       VARCHAR(512),
    home_id    UUID,
    quantity   INTEGER,
    is_bought  BOOLEAN,
    CONSTRAINT items_unique_name UNIQUE (home_id, name),
    CONSTRAINT fk_shopping_list_home_id FOREIGN KEY (home_id) REFERENCES homes (id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS barcodes
(
    id         UUID,
    barcode    VARCHAR(13) PRIMARY KEY
);

DELETE FROM homes;
INSERT INTO homes (id, name) VALUES ('b9e3c6fc-bc97-4790-9f46-623ce14b25f1', 'default home')

""")
