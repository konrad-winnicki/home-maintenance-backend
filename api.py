import uuid

import psycopg
from flask import Flask, request, jsonify
from flask_cors import CORS
from psycopg import OperationalError
from psycopg.rows import dict_row

from session import InvalidSessionCode, NoSessionCode, authenticate_user
from db import pool

app = Flask('kitchen-maintenance')
CORS(app)


class ProductAlreadyExists(Exception):
    pass


class BadRequest(Exception):
    pass


class Error(Exception):
    pass


def insert_product_to_store_positions(productId, quantity, user_id):
    query_sql = "INSERT INTO store_positions VALUES (%s, %s, %s)"
    execute_sql_query(query_sql, (productId, quantity, user_id))


def insert_product_to_shopping_list(productId, name, quantity, user_id):
    checkbox = False
    query_sql = "INSERT INTO shopping_list VALUES (%s, %s, %s, %s, %s)"
    execute_sql_query(query_sql, (productId, name, quantity, checkbox, user_id))


def add_finished_products_to_shopping_list(product_list, user_id):
    for item in product_list:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        name = item.get('name')
        try:
            insert_product_to_shopping_list(product_id, name, quantity, user_id)
        except ProductAlreadyExists:
            continue
    return "Products added to shopping list"


def insert_user_to_users(user_account_number):
    user_id = generate_unique_id()
    query_sql = "INSERT INTO users VALUES (%s, %s)"
    execute_sql_query(query_sql, (user_id, user_account_number))
    return user_id


def insert_barcode(barcode, productId, user_id):
    query_sql = "INSERT INTO barcodes VALUES (%s, %s, %s)"
    execute_sql_query(query_sql, (productId, barcode, user_id))


def insert_product(productId, name, user_id):
    query_sql = "INSERT INTO products VALUES (%s, %s, %s)"
    execute_sql_query(query_sql, (productId, name, user_id))


def insert_product_with_name(name, user_id):
    product_id = generate_unique_id()
    insert_product(product_id, name, user_id)
    return product_id


def find_tables_in_database(table_schema):
    query_sql = "select table_name from information_schema.tables where table_schema=%s"
    fetch_result = execute_fetch_all(query_sql, (table_schema,))
    tables = list(map(lambda x: x.get('table_name'), fetch_result))
    return tables


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
        return fetch_result.get("user_id")
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
    return fetch_result


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


def execute_fetch(query_sql, searched_value):
    with pool.connection() as connection:
        cursor = connection.cursor(row_factory=dict_row)
        try:
            cursor.execute(query_sql, searched_value)
            query_result = cursor.fetchone()
        except Error as e:
            print(f"The error '{e}' occurred")
        return query_result


def execute_fetch_all(query_sql, searched_value):
    with pool.connection() as connection:
        cursor = connection.cursor(row_factory=dict_row)
        try:
            cursor.execute(query_sql, searched_value)
            query_result = cursor.fetchall()
        except Error as e:
            print(f"The error '{e}' occurred")
        return query_result


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


def generate_unique_id():
    return uuid.uuid4().__str__()


def change_name(product_id, new_name, user_id):
    maybe_existing_product_id = get_product_id_by_name(new_name, user_id)
    if maybe_existing_product_id:
        replace_product_in_store_positions(product_id, maybe_existing_product_id, user_id)
    else:
        change_product_name(product_id, new_name, user_id)
    return "Product name changed"


def change_name_in_shopping_list(product_id, new_name, user_id):
    maybe_existing_product_id = get_product_id_by_name(new_name, user_id)
    if maybe_existing_product_id:
        replace_product_in_store_positions(product_id, maybe_existing_product_id, user_id)
    else:
        change_product_name_in_shopping_list(product_id, new_name, user_id)
    return "Product name changed"


def change_checkbox_status(product_id, checkbox_status, user_id):
    change_checkbox_status_in_database(product_id, checkbox_status, user_id)
    return "Checkbox status changed"


def create_tables():
    existing_tables = find_tables_in_database(table_schema='public')
    print(existing_tables)
    if 'users' not in existing_tables:
        create_table(
            """ CREATE TABLE users (user_id VARCHAR(36) PRIMARY KEY, user_account_number VARCHAR(21) UNIQUE) """)
    if 'products' not in existing_tables:
        create_table(""" CREATE TABLE products (product_id VARCHAR(36) PRIMARY KEY, name VARCHAR(500) UNIQUE, user_id VARCHAR(36) UNIQUE,
        CONSTRAINT fk_products_userId FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE) """)
    if 'store_positions' not in existing_tables:
        create_table(""" CREATE TABLE store_positions (product_id VARCHAR(36) PRIMARY KEY, quantity INTEGER, user_id VARCHAR(36) UNIQUE, 
        CONSTRAINT fk_store_productId FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE, 
        CONSTRAINT fk_store_userId FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE)
        """)
    if 'barcodes' not in existing_tables:
        create_table(""" CREATE TABLE barcodes (product_id VARCHAR(36), barcode VARCHAR(13) PRIMARY KEY,
        CONSTRAINT fk_b FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE)""")


def create_table(table_definition):
    with pool.connection() as connection:
        try:
            connection.execute(table_definition)
            print("Table created successfully")
        except OperationalError as e:
            print(f"The error '{e}' occurred")


@app.route("/store/products/", methods=["GET"])
def get_product_from_store():
    try:
        user_id = authenticate_user()
        return get_products_from_database(user_id)
    except InvalidSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/cart/items/", methods=["GET"])
def get_product_from_shopping_list():
    try:
        user_id = authenticate_user()
        return get_products_from_shoping_list(user_id)
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/", methods=["POST"])
def create_product_in_store():
    try:
        user_id = authenticate_user()
        request_body = request.json
        name = request_body.get('name')
        quantity = request_body.get('quantity')
        barcode = request_body.get("barcode")
        if barcode and name:
            return add_product_with_barcode_and_name(barcode, name, user_id)
        elif barcode:
            return add_product_with_barcode(barcode, user_id)
        elif name:
            try:
                response = add_product_with_name_to_store(name, quantity, user_id)
                return jsonify({"response": response}), 201
            except ProductAlreadyExists:
                return jsonify({"response": name + " product already exist"}), 409

        return "Name or barcode must be specified", 400

    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/delivery/", methods=["POST"])
def transfer_shopping_to_store():
    try:
        user_id = authenticate_user()
        product_list = request.json
        response = add_product_from_shopping_list(product_list, user_id)
        return jsonify({"response": response}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


def add_product_from_shopping_list(product_list, user_id):
    for item in product_list:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        name = item.get('name')
        if check_if_product_id_in_products(product_id, user_id) is None:
            insert_product(product_id, name, user_id)
        add_product_to_store_positions(product_id, quantity, user_id)
        delete_product_from_shopping_list(product_id, user_id)
    return "Products added to store"


def add_product_with_name_to_cart(name, quantity, user_id):
    existing_product_id = get_product_id_by_name(name, user_id)
    try:
        if existing_product_id:
            product_id = existing_product_id
        else:
            product_id = generate_unique_id()
        insert_product_to_shopping_list(product_id, name, quantity, user_id)

    except ProductAlreadyExists:
        raise ProductAlreadyExists
    return "Product added to database"


def add_product_with_name_to_store(name, quantity, user_id):
    existing_product_id = get_product_id_by_name(name, user_id)
    try:
        if existing_product_id:
            product_id = existing_product_id
        else:
            product_id = insert_product_with_name(name, user_id)

        insert_product_to_store_positions(product_id, quantity, user_id)

    except ProductAlreadyExists:
        raise ProductAlreadyExists
    return "Product added to database"


def add_product_with_barcode_and_name(barcode, name, user_id):
    existing_product_id = get_product_id_by_name(name, user_id)
    if existing_product_id:
        product_id = existing_product_id
    else:
        product_id = insert_product_with_name(name, user_id)

    insert_barcode(barcode, product_id)  # what if barcode already exists?
    add_product_to_store_positions(product_id, 1, user_id)
    return "Product added to database", 201


def add_product_to_store_positions(product_id, quantity, user_id):
    try:
        insert_product_to_store_positions(product_id, quantity, user_id)
    except ProductAlreadyExists:
        existing_quantity = get_quantity_by_id(product_id, user_id)
        increase_product_quantity_in_store_positions(product_id, existing_quantity + quantity, user_id)


def add_product_with_barcode(barcode, user_id):
    existing_product_id = get_product_id_for_barcode(barcode, user_id)
    if not existing_product_id:
        return "Barcode not found and name not given", 404
    add_product_to_store_positions(existing_product_id, 1, user_id)
    return "Product added to database", 201


@app.route("/cart/items/", methods=["POST"])
def create_item_at_shopping_list():
    try:
        user_id = authenticate_user()
        request_body = request.json
        name = request_body.get('name')
        quantity = request_body.get('quantity')
        barcode = request_body.get("barcode")

        if barcode and name:
            return add_product_with_barcode_and_name(barcode, name, user_id)
        elif barcode:
            return add_product_with_barcode(barcode, user_id)
        elif name:
            try:
                response = add_product_with_name_to_cart(name, quantity, user_id)
                return jsonify({"response": response}), 201
            except ProductAlreadyExists:
                return jsonify({"response": name + " product already exist"}), 409

        return "Name or barcode must be specified", 400
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/cart/items/shoppinglist", methods=["POST"])
def transfer_item_from_store_to_shopping_list():
    try:
        user_id = authenticate_user()
        product_list = request.json
        response = add_finished_products_to_shopping_list(product_list, user_id)
        return jsonify({"response": response}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/<id>", methods=["DELETE"])
def delete_product_from_store(id):
    try:
        user_id = authenticate_user()
        product_id = id

        if product_id is None:
            return "Product not found", 422
        try:
            delete_product_from_store_positions(product_id, user_id)
        except Error:
            return "DatabaseError", 500
        return jsonify({"response": "Product deleted from store positions"}), 200
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/cart/items/<id>", methods=["DELETE"])
def delete_product_from_cart(id):
    try:
        user_id = authenticate_user()
        product_id = id

        if product_id is None:
            return "422", 422
        try:
            delete_product_from_shopping_list(product_id, user_id)
        except Error:
            return "500", 500
        return jsonify({"response": "Product deleted from shopping list"}), 200
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/<id>", methods=["PUT", "PATCH"])
def update_product_in_store(id):
    try:
        user_id = authenticate_user()
        request_body = request.json
        quantity = request_body.get('quantity')
        name = request_body.get('name')
        product_id = id
        if (product_id or name or quantity) is None:
            return "422", 422
        try:
            increase_product_quantity_in_store_positions(product_id, quantity, user_id)
            change_name(product_id, name, user_id)
            result = "Product data updated"

        except ProductAlreadyExists:
            return jsonify({"response": name + " product already exist"}), 409
        except Error:
            return "DatabaseError", 500

        return jsonify({"response": result}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/cart/items/<id>", methods=["PUT", "PATCH"])
def update_product_in_shopping_list(id):
    try:
        user_id = authenticate_user()
        request_data = request.json
        check_box_status = request_data.get("checkout")
        quantity = request_data.get('quantity')
        name = request_data.get('name')
        product_id = id
        if (product_id or name or quantity or check_box_status) is None:
            return "422", 422
        try:
            change_quantity_in_shopping_list(product_id, quantity, user_id)
            change_name_in_shopping_list(product_id, name, user_id)
            change_checkbox_status(product_id, check_box_status, user_id)
            result = "Product data updated"
        except ProductAlreadyExists:
            return jsonify({"response": name + " product already exist"}), 409
        except Error:
            return "500", 500
        return jsonify({"response": result}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
