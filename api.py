from flask import Flask, request, jsonify
from flask_cors import CORS

from errors import DatabaseError
from persistence import get_products_from_database, \
    get_products_from_shoping_list, delete_product_from_shopping_list, \
    increase_product_quantity_in_store_positions, delete_product_from_store_positions, change_quantity_in_shopping_list
from services import add_product_with_barcode_and_name, add_product_with_barcode, add_product_with_name_to_store, \
    ProductAlreadyExists, add_product_from_shopping_list, add_product_with_name_to_cart, \
    add_finished_products_to_shopping_list, change_name, change_name_in_shopping_list, change_checkbox_status
from session import InvalidSessionCode, NoSessionCode, authenticate_user

app = Flask('kitchen-maintenance')
CORS(app)


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
        except DatabaseError:
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
        except DatabaseError:
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
        except DatabaseError:
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
        except DatabaseError:
            return "500", 500
        return jsonify({"response": result}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
