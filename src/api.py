from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_socketio import SocketIO, join_room
from socketio import exceptions

from errors import DatabaseError, NoSessionCode, InvalidSessionCode, ResourceNotExists
from oauth import oauth2_code_callback
from persistence import get_products, \
    get_shopping_list_items, delete_shopping_list_item, \
    update_product, delete_product, update_shopping_list_item, get_homes
from services import add_product, \
    ResourceAlreadyExists, add_bought_shopping_items, add_shopping_list_item, \
    add_missing_products_to_shopping_list, assign_user_to_home, add_home
from session import authenticate_user
from errors import SocketHandShakeError
from session import verify_session

app = Flask('kitchen-maintenance')
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*")


# TODO: remove when passed from requests
SOME_HOME_ID = 'b9e3c6fc-bc97-4790-9f46-623ce14b25f1'
#SOME_HOME_ID = 'd82fa28d-8be5-4faf-a437-d412f7132684'



@app.route("/code/callback")
def oauth_callback():
    return oauth2_code_callback()


@app.route("/homes", methods=["POST"])
def add_home_route():
    try:
        user_id = authenticate_user()
        request_body = request.json
        name = request_body.get('name')
        if name is None:
            return jsonify({"response": "Missing required attribute"}), 400

        home_id = add_home(name, user_id)
        # headers = {'Location': f'/homes/{home_id}'} TODO
        response = make_response()
        response.status_code = 201
        response.location = f'/homes/{home_id}'
        return response

    # TODO: common exception handler
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


@app.route("/homes", methods=["GET"])
def get_homes_route():
    try:
        user_id = authenticate_user()
        return get_homes(user_id)
    except (InvalidSessionCode, NoSessionCode):
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


@app.route("/homes/<home_id>/members", methods=["POST"])
def add_home_member(home_id):
    try:
        user_id = authenticate_user()
        assign_user_to_home(home_id, user_id)
        response = make_response()
        response.status_code = 204
        return response

    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except ResourceAlreadyExists:
        return jsonify({"response": user_id + " belong to this home"}), 409
    except Exception as e:
        print(e)
        return "Unknown error", 500


@app.route("/store/products/", methods=["GET"])
def get_products_route():
    try:
        user_id = authenticate_user()
        user_context = (user_id, SOME_HOME_ID)
        return get_products(user_context)
    except (InvalidSessionCode, NoSessionCode):
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


@app.route("/store/products/", methods=["POST"])
def add_product_route():
    try:
        user_id = authenticate_user()
        user_context = (user_id, SOME_HOME_ID)
        request_body = request.json
        name = request_body.get('name')
        quantity = request_body.get('quantity')
        if (name and quantity) is None:
            return jsonify({"response": "Missing required attribute"}), 400
        try:
            product_id = add_product(name, quantity, user_context)
            headers = {'Location': f'/store/products/{product_id}'}
            return jsonify({"productId": product_id}), 201, headers  # TODO: remove body
        except ResourceAlreadyExists:
            return jsonify({"response": name + " product already exist"}), 409

    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


@app.route("/store/products/<id>", methods=["PUT"])
def update_product_route(id):
    try:
        user_id = authenticate_user()
        user_context = (user_id, SOME_HOME_ID)
        request_body = request.json
        quantity = request_body.get('quantity')
        name = request_body.get('name')
        product_id = id
        if (product_id and name and quantity) is None:
            return jsonify({"response": "Missing required attributes and parameters"}), 400
        try:
            update_product(product_id, name, quantity, user_context)
            result = "Product data updated"
        except ResourceAlreadyExists:
            return jsonify({"response": name + " product name already in use"}), 409
        except DatabaseError:
            return "DatabaseError", 500

        return jsonify({"response": result}), 200
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


@app.route("/store/products/<id>", methods=["DELETE"])
def delete_product_route(id):
    try:
        user_id = authenticate_user()
        user_context = (user_id, SOME_HOME_ID)
        product_id = id
        if product_id is None:
            return jsonify({"response": "Missing required parameter"}), 400
        try:
            delete_product(product_id, user_context)

        except DatabaseError as e:
            return jsonify({"response": "DatabaseError"}), 500
        except ResourceNotExists:
            return jsonify({"response": f'Product with id {product_id} not exists'}), 404

        return jsonify({"response": "Product deleted from store positions"}), 200

    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


@app.route("/cart/items/", methods=["POST"])
def add_shopping_list_item_route():
    try:
        user_id = authenticate_user()
        user_context = (user_id, SOME_HOME_ID)
        request_body = request.json
        name = request_body.get('name')
        quantity = request_body.get('quantity')
        if (name and quantity) is None:
            return jsonify({"response": "Missing required attribute"}), 400

        try:
            item_id = add_shopping_list_item(name, quantity, user_context)
            headers = {'Location': f'/cart/items/{item_id}'}
            socketio.emit('updateShoppingItems', room=SOME_HOME_ID)

            return ({"response": item_id}), 201, headers  # TODO: remove body
        except ResourceAlreadyExists:
            return jsonify({"response": name + " product already exist"}), 409


    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


@app.route("/cart/items/", methods=["GET"])
def get_shopping_list_items_route():
    try:
        user_id = authenticate_user()
        user_context = (user_id, SOME_HOME_ID)
        return get_shopping_list_items(user_context)
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


# TODO: move to POST /delivery
@app.route("/store/products/delivery/", methods=["POST"])
def add_bought_shopping_items_route():
    try:
        user_id = authenticate_user()
        user_context = (user_id, SOME_HOME_ID)
        response = add_bought_shopping_items(user_context)
        socketio.emit('updateShoppingItems', room=SOME_HOME_ID)
        return jsonify({"response": response}), 200
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


# TODO: move to POST /transfers or /store/transfer
@app.route("/cart/items/shoppinglist", methods=["POST"])
def add_missing_products_to_shopping_list_route():
    try:
        user_id = authenticate_user()
        user_context = (user_id, SOME_HOME_ID)
        response = add_missing_products_to_shopping_list(user_context)
        socketio.emit('updateShoppingItems', room=SOME_HOME_ID)

        return jsonify({"response": response}), 201
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


@app.route("/cart/items/<id>", methods=["DELETE"])
def delete_shopping_list_item_route(id):
    try:
        user_id = authenticate_user()
        user_context = (user_id, SOME_HOME_ID)
        item_id = id
        if item_id is None:
            return jsonify({"response": "Missing required attribute"}), 400
        try:
            delete_shopping_list_item(item_id, user_context)
        except DatabaseError:
            return "DatabaseError", 500
        except ResourceNotExists:
            return jsonify({"response": f'Item with id {item_id} not exists'}), 404

        socketio.emit('updateShoppingItems', room=SOME_HOME_ID)
        return jsonify({"response": "Product deleted from shopping list"}), 200
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


@app.route("/cart/items/<id>", methods=["PUT", "PATCH"])
def update_shopping_item_route(id):
    try:
        user_id = authenticate_user()
        user_context = (user_id, SOME_HOME_ID)
        request_data = request.json
        is_bought = request_data.get("is_bought")
        quantity = request_data.get('quantity')
        name = request_data.get('name')
        item_id = id
        # FIXME: invalid use of or and None
        if (item_id and name and quantity and is_bought) is None:
            return jsonify({"response": "Missing required attribute"}), 400

        try:
            update_shopping_list_item(item_id, name, quantity, is_bought, user_context)
            result = "Shopping list item updated"
        except ResourceAlreadyExists:
            return jsonify({"response": name + " shopping list item already exists"}), 409
        except DatabaseError:
            return "500", 500
        print('itenupdate')
        socketio.emit('updateShoppingItems', room=SOME_HOME_ID)
        return jsonify({"response": result}), 200
    except InvalidSessionCode or NoSessionCode:
        return jsonify({"response": "non-authorized"}), 401
    except Exception as e:
        print(e)
        return "Unknown error", 500


@socketio.on('connect')
def socket_connection(auth):
    print(auth)
    try:
        session_code = auth['session_code']
        home = auth['home_context']
        if not session_code and home :
            raise SocketHandShakeError
        user_id = verify_session(session_code)
        join_room(home)
        print('Socked connected')
    except SocketHandShakeError:
        raise exceptions.AuthenticationError('Invalid token')


@socketio.on('disconnect')
def socket_disconnection():
    print('Client disconnected')
