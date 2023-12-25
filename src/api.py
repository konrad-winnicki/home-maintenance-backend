from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_socketio import SocketIO, join_room

from errors import SocketHandShakeError
from errors import error_handler
from oauth import oauth2_code_callback
from persistence import get_products, \
    get_shopping_list_items, delete_shopping_list_item, \
    update_product, delete_product, update_shopping_list_item, get_homes, delete_user_from_home
from services import add_product, \
    add_bought_shopping_items, add_shopping_list_item, \
    add_missing_products_to_shopping_list, assign_user_to_home, add_home, check_membership
from session import authenticate_user
from session import verify_session
from request_guard import request_guard

app = Flask('kitchen-maintenance')
CORS(app, expose_headers=['Location'])

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

        expected_req_body = {'name': str, 'email': str}
        request_guard(request_body, expected_req_body)

        name = request_body.get('name')
        home_id = add_home(name, user_id)
        response = make_response()
        response.location = f'/homes/{home_id}'
        return response, 201

    except Exception as e:
        return error_handler(e)





@app.route("/homes", methods=["GET"])
def get_homes_route():
    try:
        user_id = authenticate_user()
        return get_homes(user_id)
    except Exception as e:
        return error_handler(e)


@app.route("/homes/<home_id>/members", methods=["POST"])
def add_home_member(home_id):
    try:
        user_id = authenticate_user()
        assign_user_to_home(home_id, user_id)
        response = make_response()
        response.status_code = 204
        return response

    except Exception as e:
        return error_handler(e)



@app.route("/homes/<home_id>/members/<id>", methods=["DELETE"])
def delete_home_member(home_id, id):
    try:
        authenticate_user()
        check_membership(home_id, id)
        user_context = (id, home_id)

        delete_user_from_home(user_context)
        return jsonify({"response": "User deleted from home"}), 200

    except Exception as e:
        return error_handler(e)


PRODUCTS_URI = "/homes/<home_id>/store/products"
PRODUCT_URI = f'{PRODUCTS_URI}/<product_id>'



@app.route(PRODUCTS_URI, methods=["GET"])
def get_products_route(home_id):
    try:
        user_id = authenticate_user()
        check_membership(home_id, user_id)
        user_context = (user_id, home_id)
        return get_products(user_context)
    except Exception as e:
        return error_handler(e)

#TODO: in all endpoints check if user belongs to home
@app.route(PRODUCTS_URI, methods=["POST"])
def add_product_route(home_id):
    try:


        request_path = request.path
        user_id = authenticate_user()

        request_body = request.json
        expected_req_body = {'name': str, 'quantity': int}
        request_guard(request_body, expected_req_body)

        check_membership(home_id, user_id)
        user_context = (user_id, home_id)
        name = request_body.get('name')
        quantity = request_body.get('quantity')

        product_id = add_product(name, quantity, user_context)
        headers = {'Location': f'{request_path}/{product_id}'}
        return jsonify({"productId": product_id}), 201, headers  # TODO: remove body


    except Exception as e:
        return error_handler(e)



@app.route(PRODUCT_URI, methods=["PUT"])
def update_product_route(home_id, product_id):
    try:
        user_id = authenticate_user()
        request_body = request.json
        expected_req_body = {'name': str, 'quantity': int}
        request_guard(request_body, expected_req_body)

        check_membership(home_id, user_id)
        user_context = (user_id, home_id)
        quantity = request_body.get('quantity')
        name = request_body.get('name')

        update_product(product_id, name, quantity, user_context)
        return jsonify({"response": 'product data updated'}), 200
    except Exception as e:
        return error_handler(e)


@app.route(PRODUCT_URI, methods=["DELETE"])
def delete_product_route(home_id, product_id):
    try:
        user_id = authenticate_user()
        check_membership(home_id, user_id)
        user_context = (user_id, home_id)

        delete_product(product_id, user_context)
        return jsonify({"response": "Product deleted from store positions"}), 200

    except Exception as e:
        return error_handler(e)




@app.route("/homes/<home_id>/cart/items", methods=["POST"])
def add_shopping_list_item_route(home_id):
    try:
        user_id = authenticate_user()
        request_body = request.json

        expected_req_body = {'name': str, 'quantity': int}
        request_guard(request_body, expected_req_body)

        check_membership(home_id, user_id)
        user_context = (user_id, home_id)
        name = request_body.get('name')
        quantity = request_body.get('quantity')

        item_id = add_shopping_list_item(name, quantity, user_context)
        headers = {'Location': f'{request.path}/{item_id}'}
        socketio.emit('updateShoppingItems', room=home_id)
        return ({"response": item_id}), 201, headers  # TODO: remove body

    except Exception as e:
        return error_handler(e)



@app.route("/homes/<home_id>/cart/items", methods=["GET"])
def get_shopping_list_items_route(home_id):
    try:
        user_id = authenticate_user()
        check_membership(home_id, user_id)

        user_context = (user_id, home_id)
        return get_shopping_list_items(user_context)
    except Exception as e:
        return error_handler(e)


# TODO: move to POST /delivery
@app.route("/homes/<home_id>/store/products/delivery", methods=["POST"])
def add_bought_shopping_items_route(home_id):
    try:
        user_id = authenticate_user()
        check_membership(home_id, user_id)
        user_context = (user_id, home_id)
        response = add_bought_shopping_items(user_context)
        socketio.emit('updateShoppingItems', room=home_id)
        return jsonify({"response": response}), 200
    except Exception as e:
        return error_handler(e)


# TODO: move to POST /transfers or /store/transfer
@app.route("/homes/<home_id>/cart/items/shoppinglist", methods=["POST"])
def add_missing_products_to_shopping_list_route(home_id):
    try:
        user_id = authenticate_user()
        check_membership(home_id, user_id)
        user_context = (user_id, home_id)
        response = add_missing_products_to_shopping_list(user_context)
        socketio.emit('updateShoppingItems', room=home_id)

        return jsonify({"response": response}), 201
    except Exception as e:
        return error_handler(e)


@app.route("/homes/<home_id>/cart/items/<id>", methods=["DELETE"])
def delete_shopping_list_item_route(home_id, id):
    try:
        user_id = authenticate_user()
        check_membership(home_id, user_id)
        user_context = (user_id, home_id)
        item_id = id

        delete_shopping_list_item(item_id, user_context)
        socketio.emit('updateShoppingItems', room=home_id)
        return jsonify({"response": "Product deleted from shopping list"}), 200

    except Exception as e:
        return error_handler(e)


@app.route("/homes/<home_id>/cart/items/<id>", methods=["PUT", "PATCH"])
def update_shopping_item_route(home_id, id):
    try:
        user_id = authenticate_user()
        check_membership(home_id, user_id)
        user_context = (user_id, home_id)
        request_body = request.json
        expected_req_body = {'name': str, 'quantity': int, 'is_bought': bool}
        request_guard(request_body, expected_req_body)

        is_bought = request_body.get("is_bought")
        quantity = request_body.get('quantity')
        name = request_body.get('name')
        item_id = id
        # FIXME: invalid use of or and None
        if (item_id and name and quantity and is_bought) is None:
            return jsonify({"response": "Missing required attribute"}), 400

        update_shopping_list_item(item_id, name, quantity, is_bought, user_context)
        socketio.emit('updateShoppingItems', room=home_id)
        return jsonify({"response": 'shopping list item updated'}), 200
    except Exception as e:
        return error_handler(e)



@socketio.on('connect')
def socket_connection(auth):
    try:
        session_code = auth['session_code']
        home = auth['home_context']
        if not session_code and home :
            raise SocketHandShakeError
        verify_session(session_code)
        join_room(home)
        print('Socked connected')
    except Exception as e:
        return error_handler(e)
        #raise exceptions.AuthenticationError('Invalid token')


@socketio.on('disconnect')
def socket_disconnection():
    print('Client disconnected')
