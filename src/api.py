from flask import Flask, request, jsonify
from flask_cors import CORS

from errors import DatabaseError
from persistence import get_products, \
    get_products_from_shoping_list, delete_product_from_shopping_list, \
    increase_product_quantity_in_products, delete_from_products, change_quantity_in_shopping_list
from services import add_product_with_barcode_and_name, add_product_with_barcode, add_product, \
    ProductAlreadyExists, add_product_from_shopping_list, add_product_with_name_to_cart, \
    add_finished_products_to_shopping_list, change_name, change_name_in_shopping_list, change_checkbox_status
from session import InvalidSessionCode, NoSessionCode, authenticate_user
from src.oauth import oauth2_code_callback

app = Flask('kitchen-maintenance')
CORS(app)

@app.route("/code/callback")
def oauth_callback():
    return oauth2_code_callback()

@app.route("/store/products/", methods=["GET"])
def get_products_route():
    try:
        user_id = authenticate_user()
        return get_products(user_id)
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/", methods=["POST"])
def add_product_route():
    try:
        user_id = authenticate_user()
        request_body = request.json
        name = request_body.get('name')
        quantity = request_body.get('quantity')
        if not name or not quantity:
            return jsonify({"response": "Missing required attribute"}), 400
        try:
            product_id = add_product(name, quantity, user_id)
            return jsonify({"productId": product_id}), 201
        except ProductAlreadyExists:
            return jsonify({"response": name + " product already exist"}), 409

    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/<id>", methods=["PUT", "PATCH"])
def update_product_in_products_route(id):
    try:
        user_id = authenticate_user()
        request_body = request.json
        quantity = request_body.get('quantity')
        name = request_body.get('name')
        product_id = id
        if (product_id or name or quantity) is None:
            return jsonify({"response": "Missing required attributes and parameters"}), 400

        try:
            increase_product_quantity_in_products(product_id, quantity, user_id)
            change_name(product_id, name, user_id)
            result = "Product data updated"

        except ProductAlreadyExists:
            return jsonify({"response": name + " product already exist"}), 409
        except DatabaseError:
            return "DatabaseError", 500

        return jsonify({"response": result}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/<id>", methods=["DELETE"])
def delete_from_products_route(id):
    try:
        user_id = authenticate_user()
        product_id = id
        if product_id is None:
            return jsonify({"response": "Missing required parameter"}), 400
        try:
            delete_from_products(product_id, user_id)
        except DatabaseError:
            return "DatabaseError", 500
        return jsonify({"response": "Product deleted from store positions"}), 200
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/cart/items/", methods=["POST"])
def add_product_to_shopping_list_route():
    try:
        user_id = authenticate_user()
        request_body = request.json
        name = request_body.get('name')
        quantity = request_body.get('quantity')
        if (name or quantity) is None:
            return jsonify({"response": "Missing required attribute"}), 400

        try:
            response = add_product_with_name_to_cart(name, quantity, user_id)
            return jsonify({"response": response}), 201
        except ProductAlreadyExists:
            return jsonify({"response": name + " product already exist"}), 409

    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401



@app.route("/cart/items/", methods=["GET"])
def get_product_from_shopping_list():
    try:
        user_id = authenticate_user()
        return get_products_from_shoping_list(user_id)
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




@app.route("/cart/items/shoppinglist", methods=["POST"])
def transfer_item_from_store_to_shopping_list():
    try:
        user_id = authenticate_user()
        product_list = request.json
        response = add_finished_products_to_shopping_list(product_list, user_id)
        return jsonify({"response": response}), 201
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
