import os
import json
import datetime
import jwt
from psycopg.rows import dict_row
from flask import Flask, redirect, request, url_for, jsonify, render_template, session

from flask_login import LoginManager
from datetime import datetime, timezone, timedelta
from flask_cors import CORS

import uuid
import psycopg
from psycopg import OperationalError
from decouple import config

from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

from db import pool

# from flask_session import Session

active_sessions = {}

# TODO zwrocic tylko status, dodac zwrotny response do wyswietlenia
app = Flask('kitchen-maintenance')
# app.config['SESSION_PERMANENT'] = True
# app.config['SESSION_TYPE'] = 'filesystem'
# app.config['SESSION_FILE_DIR'] = "C:/Users/konrad/pythonProject/kitchen_maintenance_class/sessions/"
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
# app.config['SECRET_KEY'] = "ala"
# sess = Session()
# sess.init_app(app)
CORS(app)

# OAUTH.2

GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", None)
SECRET_KEY = config("SECRET_KEY", None)
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
callback_url = config('CALLBACK_URL')
redirect_url_with_token = config('REDIRECT_URL_WITH_TOKEN')
client = WebApplicationClient(GOOGLE_CLIENT_ID)


# OAUTH.2


class ProductAlreadyExists(Exception):
    pass

class NotValidSessionCode(Exception):
    pass

class BadRequest(Exception):
    pass
class NotSessionCode(Exception):
    pass
class Error(Exception):
    pass


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


def get_token(code):
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    print("request url in get token:", request.url)
    print("redirect url in get token: ", request.base_url)
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url.replace("http", "https"),
        redirect_url=request.base_url

    )

    print("GetTokenRequest Url:", token_url)
    print("GetTokenRequest Headers:", headers)
    print("GetTokenRequest Body:", body)
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    return client.parse_request_body_response(json.dumps(token_response.json()))


def get_user_info():
    google_provider_cfg = get_google_provider_cfg()
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    print('user info', headers)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        return unique_id
    else:
        return "denied"


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
    print(pool.get_stats())  # TODO: remove
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


def check_if_user_has_active_session(request):
    session_code = request.headers.get("Authorization")
    user_id = active_sessions.get(session_code)
    return user_id


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
        create_table(""" CREATE TABLE users (user_id VARCHAR(36) PRIMARY KEY, user_account_number VARCHAR(21) UNIQUE) """)
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

def authorization_verification(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms="HS256")
        user_id = payload.get('user_id')
        return user_id
    except jwt.ExpiredSignatureError:
        raise NotValidSessionCode


def check_if_session_code():
    session_code = request.headers.get("Authorization")
    if not session_code:
        raise NotSessionCode
    return session_code



@app.route("/store/products/", methods=["GET"])
def get_product_from_store():
    try:
        session_code = check_if_session_code()
        user_id = authorization_verification(session_code)
        return get_products_from_database(user_id)
    except NotValidSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/cart/items/", methods=["GET"])
def get_product_from_shopping_list():
    try:
        session_code = check_if_session_code()
        user_id = authorization_verification(session_code)
        return get_products_from_shoping_list(user_id)
    except NotValidSessionCode or NotSessionCode:
        return jsonify({"response": "non-authorized"}), 401



@app.route("/store/products/", methods=["POST"])
def create_product_in_store():
    try:
        session_code = check_if_session_code()
        user_id = authorization_verification(session_code)
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

    except NotValidSessionCode or NotSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/delivery/", methods=["POST"])
def transfer_shopping_to_store():
    try:
        session_code = check_if_session_code()
        user_id = authorization_verification(session_code)
        product_list = request.json
        response = add_product_from_shopping_list(product_list, user_id)
        return jsonify({"response": response}), 201
    except NotValidSessionCode or NotSessionCode:
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
        session_code = check_if_session_code()
        user_id = authorization_verification(session_code)
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
    except NotValidSessionCode or NotSessionCode:
        return jsonify({"response": "non-authorized"}), 401

@app.route("/cart/items/shoppinglist", methods=["POST"])
def transfer_item_from_store_to_shopping_list():
    try:
        session_code = check_if_session_code()
        user_id = authorization_verification(session_code)
        product_list = request.json
        response = add_finished_products_to_shopping_list(product_list, user_id)
        return jsonify({"response": response}), 201
    except NotValidSessionCode or NotSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/<id>", methods=["DELETE"])
def delete_product_from_store(id):
    try:
        session_code = check_if_session_code()
        user_id = authorization_verification(session_code)
        product_id = id

        if product_id is None:
            return "Product not found", 422
        try:
            delete_product_from_store_positions(product_id, user_id)
        except Error:
            return "DatabaseError", 500
        return jsonify({"response": "Product deleted from store positions"}), 200
    except NotValidSessionCode or NotSessionCode:
        return jsonify({"response": "non-authorized"}), 401

@app.route("/cart/items/<id>", methods=["DELETE"])
def delete_product_from_cart(id):
    try:
        session_code = check_if_session_code()
        user_id = authorization_verification(session_code)
        product_id = id

        if product_id is None:
            return "422", 422
        try:
            delete_product_from_shopping_list(product_id, user_id)
        except Error:
            return "500", 500
        return jsonify({"response": "Product deleted from shopping list"}), 200
    except NotValidSessionCode or NotSessionCode:
        return jsonify({"response": "non-authorized"}), 401

@app.route("/store/products/<id>", methods=["PUT", "PATCH"])
def update_product_in_store(id):
    try:
        session_code = check_if_session_code()
        user_id = authorization_verification(session_code)
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
    except NotValidSessionCode or NotSessionCode:
        return jsonify({"response": "non-authorized"}), 401

@app.route("/cart/items/<id>", methods=["PUT", "PATCH"])
def update_product_in_shopping_list(id):
    try:
        session_code = check_if_session_code()
        user_id = authorization_verification(session_code)
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
    except NotValidSessionCode or NotSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/code/callback")
def callback():
    code33 = request.args.get("code")
    response = get_token(code33)
    id_token = response['id_token']
    decoded_token = jwt.decode(id_token, options={"verify_signature": False})
    user_account_number = decoded_token['sub']
    print("user account", user_account_number)
    if user_account_number != "denied":
        print("LOGGED")
        user_id = get_user_from_users(user_account_number)
        if not user_id:
            user_id = insert_user_to_users(user_account_number)
        current_time = datetime.now(tz=timezone.utc)
        session_duration = timedelta(minutes=1)
        session_code = jwt.encode({"user_id": user_id, "exp": current_time + session_duration}, SECRET_KEY)
        return redirect('http://localhost:3000?session_code=' + session_code)




# the http server is run manually only during local development
on_local_environment = os.getenv('FLY_APP_NAME') is None
print('on_local_env:', on_local_environment)
if on_local_environment:
    create_tables()
    app.run(
        #debug=False,
            #ssl_context=('cert/cert.pem', 'cert/priv_key.pem')
            )

else:
    create_tables()
