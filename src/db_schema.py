from src.db import create_schema


def create_tables():
    create_schema(table_schame + functions + triggers)



table_schame =    """
CREATE TABLE IF NOT EXISTS users
(
    id                  UUID PRIMARY KEY,
    user_account_number VARCHAR(128) UNIQUE,
    email               VARCHAR(128) UNIQUE
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
    CONSTRAINT quantity CHECK (quantity >= 0),
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
    CONSTRAINT quantity CHECK (quantity >= 0),
    CONSTRAINT items_unique_name UNIQUE (home_id, name),
    CONSTRAINT fk_shopping_list_home_id FOREIGN KEY (home_id) REFERENCES homes (id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS barcodes
(
    id         UUID,
    barcode    VARCHAR(13) PRIMARY KEY
);

"""

functions = """
CREATE or REPLACE FUNCTION delete_home_if_last_member_deleted()
RETURNS TRIGGER AS $delete_home$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM home_members WHERE home_id = OLD.home_id
    ) THEN
        DELETE FROM homes WHERE id = OLD.home_id;
    END IF;
    RETURN OLD;
END;
$delete_home$ LANGUAGE plpgsql;
"""

triggers = """
CREATE OR REPLACE TRIGGER delete_home
AFTER DELETE ON home_members
FOR EACH ROW EXECUTE FUNCTION delete_home_if_last_member_deleted();
"""
