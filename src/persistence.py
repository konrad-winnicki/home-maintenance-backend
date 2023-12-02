import psycopg
from psycopg import Error
from psycopg.rows import dict_row

from db import pool, execute_fetch
from errors import ProductAlreadyExists


def insert_product_to_store_positions(productId, quantity, user_id):
    query_sql = "INSERT INTO store_positions VALUES (%s, %s, %s)"
    execute_sql_query(query_sql, (productId, quantity, user_id))


def insert_product_to_shopping_list(productId, name, quantity, user_id):
    checkbox = False
    query_sql = "INSERT INTO shopping_list VALUES (%s, %s, %s, %s, %s)"
    execute_sql_query(query_sql, (productId, name, quantity, checkbox, user_id))



def insert_user(user_id, user_account_number):
    query_sql = "INSERT INTO users VALUES (%s, %s)"
    execute_sql_query(query_sql, (user_id, user_account_number))
    return user_id


def insert_barcode(barcode, productId, user_id):
    query_sql = "INSERT INTO barcodes VALUES (%s, %s, %s)"
    execute_sql_query(query_sql, (productId, barcode, user_id))


def insert_product(product_id, name, quantity, user_id):
    query_sql = "INSERT INTO products (product_id, name, quantity, user_id) VALUES (%s, %s, %s, %s)"
    execute_sql_query(query_sql, (product_id, name, quantity, user_id))


def insert_product_with_name(product_id, name, user_id):
    insert_product(product_id, name, user_id)
    return product_id


def execute_sql_query(query_sql, query_values):
    with pool.connection() as connection:
        try:
            connection.execute(query_sql, query_values)
            print("Product inserted successfully")
        except psycopg.errors.UniqueViolation:
            raise ProductAlreadyExists
        except Error as err:
            print(err)
        return "Product added to database"


def get_products_from_database(user_id):
    query_sql = 'select store_positions.product_id, name, quantity from store_positions join products on store_positions.product_id = products.product_id where store_positions.user_id=%s order by products.name'
    with pool.connection() as connection:
        cursor = connection.cursor(row_factory=dict_row)
        try:
            cursor.execute(query_sql, (user_id,))
            result = []
            for row in cursor.fetchall():
                result.append({"product_id": row["product_id"], "quantity": row["quantity"], "name": row["name"]})
            return result
        except Error as e:
            print(f"The error '{e}' occurred")


def get_products_from_shoping_list(user_id):
    query_sql = 'select product_id, name, quantity, checkout from shopping_list where user_id=%s order by name'
    with pool.connection() as connection:
        cursor = connection.cursor(row_factory=dict_row)

        try:
            cursor.execute(query_sql, (user_id,))
            result = []

            for row in cursor.fetchall():
                result.append({"product_id": row["product_id"], "quantity": row["quantity"], "name": row["name"],
                               "checkout": row["checkout"]})
            return result
        except Error as e:
            print(f"The error '{e}' occurred")


def get_user_from_users(user_account_number):
    query_sql = "select * from users where user_account_number=%s"
    fetch_result = execute_fetch(query_sql, (user_account_number,))
    if fetch_result:
        user_id = fetch_result.get("user_id")
        return user_id
    return fetch_result


def get_product_id_for_barcode(barcode, user_id):
    query_sql = "select * from barcodes where barcode=%s and user_id=%s"
    fetch_result = execute_fetch(query_sql, (barcode, user_id,))
    if fetch_result:
        return fetch_result.get("product_id")
    return fetch_result


def get_product_id_by_name(name, user_id):
    query_sql = "select * from products where name=%s and user_id=%s"
    fetch_result = execute_fetch(query_sql, (name, user_id,))
    if fetch_result:
        return fetch_result.get("product_id")
    return None


def get_quantity_by_id(product_id, user_id):
    query_sql = "select * from store_positions where product_id=%s and user_id=%s"
    fetch_result = execute_fetch(query_sql, (product_id, user_id,))
    if fetch_result:
        return fetch_result.get("quantity")
    return fetch_result


def check_if_product_id_in_products(product_id, user_id):
    query_sql = "select * from products where product_id=%s and user_id=%s"
    fetch_result = execute_fetch(query_sql, (product_id, user_id,))
    if fetch_result:
        return fetch_result.get("product_id")
    return fetch_result


#######
def get_product_id_by_name_from_shoping_list(name, user_id):
    query_sql = "select * from shopping_list where name=%s and user_id=%s"
    fetch_result = execute_fetch(query_sql, (name, user_id,))
    if fetch_result:
        return fetch_result.get("product_id")
    return fetch_result




def delete_product_from_store_positions(product_id, user_id):
    query_sql = "DELETE FROM store_positions WHERE product_id=%s and user_id=%s"
    execute_sql_query(query_sql, (product_id, user_id,))


def delete_product_from_shopping_list(product_id, user_id):
    query_sql = "DELETE FROM shopping_list WHERE product_id=%s and user_id=%s"
    execute_sql_query(query_sql, (product_id, user_id,))


def increase_product_quantity_in_store_positions(product_id, quantity, user_id):
    query_sql = "update store_positions SET quantity=%s where product_id=%s and user_id=%s"
    execute_sql_query(query_sql, (quantity, product_id, user_id,))
    return "Product quantity changed"


def change_product_name(product_id, name, user_id):
    query_sql = "update products SET name=%s where product_id=%s and user_id=%s"
    execute_sql_query(query_sql, (name, product_id, user_id,))
    return "Product name changed in database"


def change_quantity_in_store(product_id, quantity, user_id):
    query_sql = "update store_positions SET quantity=%s where product_id=%s and user_id=%s"
    execute_sql_query(query_sql, (quantity, product_id, user_id,))
    return "Product quantity changed in database"


def change_quantity_in_shopping_list(product_id, quantity, user_id):
    query_sql = "update shopping_list SET quantity=%s where product_id=%s and user_id=%s"
    execute_sql_query(query_sql, (quantity, product_id, user_id,))
    return "Product quantity changed in database"


def change_product_name_in_shopping_list(product_id, name, user_id):
    query_sql = "update shopping_list SET name=%s where product_id=%s and user_id=%s"
    execute_sql_query(query_sql, (name, product_id, user_id,))
    return "Product name changed in database"


def change_checkbox_status_in_database(product_id, checkbox_status, user_id):
    query_sql = "update shopping_list SET checkout=%s where product_id=%s and user_id=%s"
    execute_sql_query(query_sql, (checkbox_status, product_id, user_id,))
    return "Product name changed in database"


def replace_product_in_store_positions(product_id, new_id, user_id):
    query_sql = "update store_positions SET product_id=%s where product_id=%s and user_id=%s"
    execute_sql_query(query_sql, (new_id, product_id, user_id,))
    return "Product name changed in database"


def replace_product_in_shopping_list(product_id, new_id, user_id):
    query_sql = "update shopping_list SET product_id=%s where product_id=%s and user_id=%s"
    execute_sql_query(query_sql, (new_id, product_id, user_id,))
    return "Product name changed in database"




