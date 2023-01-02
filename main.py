import os
from json import JSONEncoder
from json import JSONDecoder
import jsonpickle
from flask import Flask, jsonify
from flask import request
from flask import current_app
from flask_cors import CORS
import json
import uuid


# TODO zwrocic tylko status, dodac zwrotny response do wyswietlenia
app = Flask('kitchen-maintenance')
CORS(app)

class ProductAlreadyExists(Exception):
    pass

class ProductDoesNotExists(Exception):
    pass

class ProductOnlyInBarcodeDatabase(Exception):
    pass

class ProductDoesNotExist(Exception):
    pass


class Error(Exception):
    pass

class Barcode:
    def __init__(self, barcode, product_id, name):
        self.barcode = barcode
        self.product_id = product_id
        self.name = name


class Product:

    def __init__(self, product_id, name, quantity):
        self.product_id = product_id
        self.name = name
        self.quantity = quantity


file_location = ""


def save_to_json(dictionary, file_name):
    file_path = file_location + file_name
    encoded = jsonpickle.encode(dictionary)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(encoded, file)

def for_frontend(dane):
    dictionary = []
    for k, v in dane.items():
        dictionary.append(v)
    return jsonpickle.encode(dictionary, unpicklable=False)






def open_json(file_name):
    file_path = file_location + file_name
    if not os.path.exists(file_path):
        with open(file_path, "wt", encoding="utf-8") as file:
            file.write("\"{}\"")

    with open(file_path, "r", encoding="utf-8") as file:
        encoded_data = json.load(file)
        aa = jsonpickle.decode(encoded_data)

        return aa

def check_if_product_in_database(name, data_base):
    for id, object in data_base.items():
        if object.name == name:
            return True
    return False

def find_barcode_for_product_id(product_id, barcode_dtb):
    for barcode, object in barcode_dtb.items():
        if object.product_id == product_id:
            return barcode

def ad_barcode_to_database(barcode, id, name):
    list_of_barcodes = open_json("barcode_list.json")
    list_of_barcodes.update({barcode: Barcode(barcode, id, name)})
    if list_of_barcodes.get(barcode) is None:
        raise Error
    save_to_json(list_of_barcodes, "barcode_list.json")

def check_barcode_in_database(barcode):
    list_of_barcodes = open_json("barcode_list.json")
    barcode_object = list_of_barcodes.get(barcode)
    if barcode_object is None:
        raise ProductDoesNotExist
    return barcode_object


def add_product(product_name, quantity, product_id=None):
    p_id = product_id

    list_of_products = open_json("product_list.json")
    if check_if_product_in_database(product_name, list_of_products):
        raise ProductAlreadyExists
    if p_id is None:
        p_id = uuid.uuid4().__str__()
    list_of_products.update({p_id: Product(p_id, product_name, quantity)})
    if list_of_products.get(p_id) is None:
        raise Error
    save_to_json(list_of_products, "product_list.json")

    return vars(list_of_products.get(p_id))

def delete(product_id):
    product_list = open_json("product_list.json")
    check_if_product_exist = product_list.get(product_id)
    if check_if_product_exist is None:
        raise ProductDoesNotExist
    if check_if_product_exist is not None:
        del product_list[product_id]
    save_to_json(product_list, "product_list.json")
    return jsonify({product_id: "deleted"})

def change_name(product_id, former_name, new_name):
    product_list = open_json("product_list.json")
    list_of_barcodes = open_json("barcode_list.json")
    if product_list.get(product_id) is None:
        raise ProductDoesNotExist
    if check_if_product_in_database(new_name, product_list):
        raise ProductAlreadyExists
    product_list[product_id].name = new_name
    barcode = find_barcode_for_product_id(product_id, list_of_barcodes)
    if barcode is not None:
        list_of_barcodes[barcode].name = new_name
        if product_list[product_id].name != new_name:
            raise Error
    save_to_json(product_list, "product_list.json")
    save_to_json(list_of_barcodes, "barcode_list.json")
    return {"product_id": product_id, "new_name": product_list[product_id].name, "former_name": former_name}

def update_product_quantity(product_id, quantity):
    product_list = open_json("product_list.json")
    if product_list.get(product_id) is None:
        raise ProductOnlyInBarcodeDatabase
    quantity_to_change = product_list[product_id].quantity

    product_list[product_id].quantity += quantity

    if product_list[product_id].quantity == quantity_to_change:
        raise Error
    save_to_json(product_list, "product_list.json")
    return vars(product_list.get(product_id))


@app.route("/products/", methods=["GET"])
def get_product():
    plik = open_json("product_list.json")
    res = for_frontend(plik), 200
    return res


@app.route("/products/", methods=["POST"])
def create_product():
    data = request.json
    product_name = data.get('name')
    quantity = data.get('quantity')
    barcode = data.get("barcode")

    if barcode is not None and product_name is None:
        product_id = None
        product_name = None

        try:
            barcode_object = check_barcode_in_database(barcode)
            product_id = barcode_object.product_id
            product_name = barcode_object.name
            result = update_product_quantity(product_id, quantity=1)
        except ProductOnlyInBarcodeDatabase:
            try:

                added_product = add_product(product_name, 1, product_id)

                result = jsonify({"product_in_barcode_database": added_product})
                return result, 201
            except ProductAlreadyExists:
                return "Product with importing name already exists", 409

        except ProductDoesNotExist:
            return "Not exist", 404

        return result, 201

    if barcode is not None and product_name is not None:
        try:
            result = add_product(product_name, 1, product_id=None)
            product_id = result.get("product_id")
            ad_barcode_to_database(barcode, product_id, product_name)

            return result, 201
        except ProductAlreadyExists:
            return product_name + " already exists", 409
        except Error:
            return "500", 500


    if product_name is None or quantity is None:
        return "400", 400
    try:
        result = add_product(product_name, quantity, product_id=None)
    except ProductAlreadyExists:
        return product_name + " already exists", 409
    except Error:
        return "500", 500
    return result, 201

@app.route("/products/<id>", methods=["DELETE"])
def delete_product(id):
    product_id = id
    if product_id is None:
        return "422", 422
    try:
        result_of_deleting = delete(product_id)
    except ProductDoesNotExist:
        return "Product does not exist", 422
    except Error:
        return "500", 500

    return result_of_deleting, 200

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
            result = update_product_quantity(product_id, quantity)
        if request.method == "PATCH":
            name_to_change = request_data.get('name_to_change')
            new_name = request_data.get('new_name')
            if new_name is None or name_to_change is None:
                return "422", 422
            result = change_name(product_id, name_to_change, new_name)
    except ProductAlreadyExists:
        return new_name + " already exists", 409
    except ProductDoesNotExist:
        return "404", 404
    except Error:
        return "500", 500
    return result, 201


# the http server is run manually only during local development
on_local_environment = os.getenv('FLY_APP_NAME') is None
if on_local_environment:
    app.run(host="0.0.0.0", port=int("8080"), debug=True)
else:
    file_location = "/tmp/" # TODO: remove it

