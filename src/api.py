from flask import Flask, request, jsonify
from flask_cors import CORS

from errors import DatabaseError
from persistence import get_products, \
    get_shopping_list_items, delete_shopping_list_item, \
    update_product, delete_product, update_shopping_list_item
from services import add_product, \
    ResourceAlreadyExists, add_bought_shopping_items, add_shopping_list_item, \
    add_missing_products_to_shopping_list
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
        except ResourceAlreadyExists:
            return jsonify({"response": name + " product already exist"}), 409

    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/<id>", methods=["PUT"])
def update_product_route(id):
    try:
        user_id = authenticate_user()
        request_body = request.json
        quantity = request_body.get('quantity')
        name = request_body.get('name')
        product_id = id
        if (product_id or name or quantity) is None:
            return jsonify({"response": "Missing required attributes and parameters"}), 400
        try:
            update_product(product_id, name, quantity, user_id)
            result = "Product data updated"
        except ResourceAlreadyExists:
            return jsonify({"response": name + " product name already in use"}), 409
        except DatabaseError:
            return "DatabaseError", 500

        return jsonify({"response": result}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/store/products/<id>", methods=["DELETE"])
def delete_product_route(id):
    try:
        user_id = authenticate_user()
        product_id = id
        if product_id is None:
            return jsonify({"response": "Missing required parameter"}), 400
        try:
            delete_product(product_id, user_id)
        except DatabaseError:
            return "DatabaseError", 500
        return jsonify({"response": "Product deleted from store positions"}), 200
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/cart/items/", methods=["POST"])
def add_shopping_list_item_route():
    try:
        user_id = authenticate_user()
        request_body = request.json
        name = request_body.get('name')
        quantity = request_body.get('quantity')
        if (name or quantity) is None:
            return jsonify({"response": "Missing required attribute"}), 400

        try:
            response = add_shopping_list_item(name, quantity, user_id)
            return jsonify({"response": response}), 201
        except ResourceAlreadyExists:
            return jsonify({"response": name + " product already exist"}), 409

    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/cart/items/", methods=["GET"])
def get_shopping_list_items_route():
    try:
        user_id = authenticate_user()
        return get_shopping_list_items(user_id)
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


# TODO: move to POST /delivery
@app.route("/store/products/delivery/", methods=["POST"])
def add_bought_shopping_items_route():
    try:
        user_id = authenticate_user()
        response = add_bought_shopping_items(user_id)
        return jsonify({"response": response}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


# TODO: move to POST /transfers or /store/transfer
@app.route("/cart/items/shoppinglist", methods=["POST"])
def add_missing_products_to_shopping_list_route():
    try:
        user_id = authenticate_user()
        # products = request.json # TODO: remove from frontend
        response = add_missing_products_to_shopping_list(user_id)
        return jsonify({"response": response}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/cart/items/<id>", methods=["DELETE"])
def delete_shopping_list_item_route(id):
    try:
        user_id = authenticate_user()
        item_id = id
        if item_id is None:
            return jsonify({"response": "Missing required attribute"}), 400
        try:
            delete_shopping_list_item(item_id, user_id)
        except DatabaseError:
            return "DatabaseError", 500
        return jsonify({"response": "Product deleted from shopping list"}), 200
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401


@app.route("/cart/items/<id>", methods=["PUT", "PATCH"])
def update_shopping_list_item_route(id):
    try:
        user_id = authenticate_user()
        request_data = request.json
        is_bought = request_data.get("checkout")
        quantity = request_data.get('quantity')
        name = request_data.get('name')
        item_id = id
        if (item_id or name or quantity or is_bought) is None:
            return jsonify({"response": "Missing required attribute"}), 400

        try:
            update_shopping_list_item(item_id, name, quantity, is_bought, user_id)
            result = "Shopping list item updated"
        except ResourceAlreadyExists:
            return jsonify({"response": name + " shopping list item already exists"}), 409
        except DatabaseError:
            return "500", 500
        return jsonify({"response": result}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
