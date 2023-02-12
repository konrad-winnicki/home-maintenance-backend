import os

from flask import Flask, jsonify
from flask import request

from flask_cors import CORS

import uuid
import psycopg2
from psycopg2 import OperationalError, errorcodes, extras
from psycopg2.errors import UniqueViolation

# TODO zwrocic tylko status, dodac zwrotny response do wyswietlenia
app = Flask('kitchen-maintenance')
CORS(app)


class ProductAlreadyExists(Exception):
    pass


class Error(Exception):
    pass


def open_conection():
    connection = None
    try:
        connection = psycopg2.connect(
            host="postgres.c3gdxucwufp2.eu-west-2.rds.amazonaws.com",
            user="postgres",
            password="krowa333",
            port="5432",
            database="postgres"

        )
        print("Connection to PostgresSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


def close_connection(connection, cursor):
    if connection is not None:
        cursor.close()
        connection.close()
        print("Postgres SQL connection is closed")


def insert_product_to_magazyn(productId, quantity):
    query_sql = "INSERT INTO magazyn VALUES (%s, %s)"
    execute_sql_query(query_sql, (productId, quantity))


def insert_barcode(barcode, productId):
    query_sql = "INSERT INTO barcodes VALUES (%s, %s)"
    execute_sql_query(query_sql, (productId, barcode))


def insert_product(productId, name):
    query_sql = "INSERT INTO products VALUES (%s, %s)"
    execute_sql_query(query_sql, (productId, name))


def insert_product_with_name(name):
    product_id = generate_product_id()
    insert_product(product_id, name)
    return product_id


def execute_sql_query(query_sql, query_values):
    connection = open_conection()
    cursor = connection.cursor()
    try:
        cursor.execute(query_sql, query_values)
        connection.commit()
        print("Product inserted successfully")
    except UniqueViolation:
        raise ProductAlreadyExists
    except Error as err:
        print(err)
    finally:
        close_connection(connection, cursor)
    return "Product added to database"


def get_products_from_database():
    connection = open_conection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query_sql = "select magazyn.product_id, name, quantity from magazyn join products on " \
                "magazyn.product_id = products.product_id order by products.name"
    try:
        cursor.execute(query_sql)
        result = []
        for row in cursor.fetchall():
            result.append({"product_id": row["product_id"], "quantity": row["quantity"], "name": row["name"]})
        return result

    except Error as e:
        print(f"The error '{e}' occurred")
    finally:
        close_connection(connection, cursor)


def get_product_id_for_barcode(searched_value):
    query_sql = "select * from barcodes where barcode=%s"
    fetch_result = execute_fetch(query_sql, searched_value)
    if fetch_result:
        return fetch_result.get("product_id")
    return fetch_result


def get_product_id_by_name(searched_value):
    query_sql = "select * from products where name=%s"
    fetch_result = execute_fetch(query_sql, searched_value)
    if fetch_result:
        return fetch_result.get("product_id")
    return fetch_result


def execute_fetch(query_sql, searched_value):
    connection = open_conection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute(query_sql, (searched_value,))
        query_result = cursor.fetchone()
    except Error as e:
        print(f"The error '{e}' occurred")
    finally:
        close_connection(connection, cursor)
    return query_result


def delete_product_from_magazyn(product_id):
    query_sql = "DELETE FROM magazyn WHERE product_id=%s"
    execute_sql_query(query_sql, (product_id,))


def increase_product_quantity_in_magazyn(product_id, quantity):
    query_sql = "update magazyn SET quantity=quantity+%s where product_id=%s"
    execute_sql_query(query_sql, (quantity, product_id))
    return "Product quantity changed"


def change_product_name(product_id, name):
    query_sql = "update products SET name=%s where product_id=%s"
    execute_sql_query(query_sql, (name, product_id))
    return "Product name changed in database"


def replace_product_in_magazyn(product_id, new_id):
    query_sql = "update magazyn SET product_id=%s where product_id=%s"
    execute_sql_query(query_sql, (new_id, product_id))
    return "Product name changed in database"


def generate_product_id():
    return uuid.uuid4().__str__()


def change_name(product_id, new_name):
    maybe_existing_product_id = get_product_id_by_name(new_name)
    if maybe_existing_product_id:
        replace_product_in_magazyn(product_id, maybe_existing_product_id)
    else:
        change_product_name(product_id, new_name)

    return "Product name changed"


def create_tables():
    connection = open_conection()
    cursor = connection.cursor()
    tables = (
        """ CREATE TABLE products (product_id VARCHAR(36) PRIMARY KEY, name VARCHAR(500) UNIQUE) """,
        """ CREATE TABLE magazyn (product_id VARCHAR(36) PRIMARY KEY, quantity INTEGER, 
        CONSTRAINT fk_m FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE)""",
        """ CREATE TABLE barcodes (product_id VARCHAR(36), barcode VARCHAR(13) PRIMARY KEY,
        CONSTRAINT fk_b FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE)""",

    )
    try:
        for table in tables:
            print("creating table: ", table)
            cursor.execute(table)
            connection.commit()
        print("Tables established successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    finally:
        close_connection(connection, cursor)


@app.route("/products/", methods=["GET"])
def get_product():
    return get_products_from_database()


@app.route("/products/", methods=["POST"])
def create_product():
    data = request.json
    name = data.get('name')
    barcode = data.get("barcode")

    if barcode and name:
        return add_product_with_barcode_and_name(barcode, name)

    elif barcode:
        return add_product_with_barcode(barcode)

    elif name:
        return add_product_with_name(name)

    return "Name or barcode must be specified", 400


def add_product_with_name(name):
    existing_product_id = get_product_id_by_name(name)
    try:
        if existing_product_id:
            product_id = existing_product_id
        else:
            product_id = insert_product_with_name(name)

        insert_product_to_magazyn(product_id, 1)
    except ProductAlreadyExists:
        return name + " already exists", 409
    return "Product added to database", 201


def add_product_with_barcode_and_name(barcode, name):
    existing_product_id = get_product_id_by_name(name)
    if existing_product_id:
        product_id = existing_product_id
    else:
        product_id = insert_product_with_name(name)

    insert_barcode(barcode, product_id)  # what if barcode already exists?
    add_product_to_magazyn(product_id)
    return "Product added to database", 201


def add_product_to_magazyn(product_id):
    try:
        insert_product_to_magazyn(product_id, 1)
    except ProductAlreadyExists:
        increase_product_quantity_in_magazyn(product_id, 1)


def add_product_with_barcode(barcode):
    existing_product_id = get_product_id_for_barcode(barcode)
    if not existing_product_id:
        return "Barcode not found and name not given", 404
    add_product_to_magazyn(existing_product_id)
    return "Product added to database", 201


@app.route("/products/<id>", methods=["DELETE"])
def delete_product(id):
    product_id = id
    if product_id is None:
        return "422", 422
    try:
        delete_product_from_magazyn(product_id)
    except Error:
        return "500", 500
    return "Product deleted from magazyn", 200


@app.route("/products/<id>", methods=["PUT", "PATCH"])
def update_product(id):
    request_data = request.json
    product_id = id
    if product_id is None:
        return "422", 422
    try:
        if request.method == "PUT":
            quantity = request_data.get('quantity')
            if quantity is None:
                return "422", 422
            result = increase_product_quantity_in_magazyn(product_id, quantity)
        if request.method == "PATCH":
            new_name = request_data.get('new_name')
            if new_name is None:
                return "422", 422
            result = change_name(product_id, new_name)
    except ProductAlreadyExists:
        return new_name + " already exists", 409
    except Error:
        return "500", 500

    return result, 201


# the http server is run manually only during local development
on_local_environment = os.getenv('FLY_APP_NAME') is None
print('on_local_env:', on_local_environment)
if on_local_environment:
    # print('before create tables')
    # create_tables()
    app.run(host="0.0.0.0", port=int("8080"), debug=False)

else:
    print('before create tables')
    create_tables()
