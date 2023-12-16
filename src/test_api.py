import json
import os
import random
import string

import pytest
from assertpy import assert_that

from api import app
from db import execute_sql_query
from persistence import insert_user
from services import generate_unique_id
from session import create_session


def delete_all_table_contents():
    tables = ["users", "products", "shopping_list_items", "homes", "home_members"]
    list(map(lambda table: execute_sql_query("DELETE FROM " + table + ";", []), tables))


# TODO: create db schema before all tests
@pytest.fixture(autouse=True)
def clean_database():
    delete_all_table_contents()


@pytest.fixture(autouse=True)
def set_app_profile():
    os.environ['APP_PROFILE'] = 'test'


@pytest.fixture
def user_tokens():
    user_id1 = insert_user(generate_unique_id(), 'user1')
    user_id2 = insert_user(generate_unique_id(), 'user2')
    return create_session(user_id1), create_session(user_id2)


@pytest.fixture
def user_token(user_tokens):
    token1, _ = user_tokens
    return token1


def random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def random_number(min=0, max=100):
    return random.randint(min, max)


def some_product(name=None, quantity=None):
    return {'name': name if name is not None else random_string(10)
        , 'quantity': quantity if quantity is not None else random_number()}


def some_home(name=None):
    return {'name': name if name is not None else random_string(10)}


def some_shopping_item(name=None, quantity=None):
    return {'name': name if name is not None else random_string(10),
            'quantity': quantity if quantity is not None else random_number()}


def test_unauthenticated_access():
    response = app.test_client().get("/store/products/")
    assert response.status_code == 401


def test_adding_homes(user_token):
    # given
    home = some_home()

    # when
    response = (app.test_client()
                .post("/homes", headers={'Authorization': user_token},
                      json=home))

    # then
    assert response.status_code == 201
    assert_that(response.location).matches(r'/homes/[0-9a-f]+')


def test_list_homes(user_token):
    # given
    home1, home2 = [some_home(), some_home()]
    add_home(user_token, home1)
    add_home(user_token, home2)

    # when
    response = (app.test_client()
                .get("/homes", headers={'Authorization': user_token}))

    # then
    assert response.status_code == 200
    body = json.loads(response.data.decode('utf-8'))
    assert len(body) == 2
    assert_that(body).extracting('name').contains_only(home1['name'], home2['name'])
    assert_that(body).extracting('id').is_not_empty()


# TODO: invitation_code
def test_joining_existing_home(user_tokens):
    # given
    home_owner, other_user = user_tokens
    home = some_home()
    add_home(home_owner, home)

    # and
    _, home_response = list_resources(home_owner, "/homes")
    home_id = home_response[0]['id']

    # when
    response = (app.test_client()
                .post(f"/homes/{home_id}/members", headers={'Authorization': other_user}))

    # then
    assert response.status_code == 204
    _, other_user_homes = list_resources(other_user, "/homes")
    assert len(other_user_homes) == 1
    assert other_user_homes[0]['name'] == home['name']
    assert other_user_homes[0]['id'] == home_id

# TODO: test joining non-existent home

def test_adding_products(user_token):
    response1 = (app.test_client()
                 .post("/store/products/", headers={'Authorization': user_token},
                       json=some_product('Milk', 2)))
    assert response1.status_code == 201
    response2 = (app.test_client()
                 .post("/store/products/", headers={'Authorization': user_token},
                       json=some_product('Bread', 1)))
    assert response2.status_code == 201

    _, body = list_products(user_token)
    assert_that(body).extracting('name', sort='name').contains_only('Bread', 'Milk')
    assert_that(body).extracting('quantity', sort='name').contains_only(1, 2)
    assert_that(body).extracting('product_id').is_not_empty()


def test_adding_product_with_same_name_fails(user_token):
    # given
    product = some_product()
    add_product(user_token, product)

    # when
    response = (app.test_client()
                .post("/store/products/", headers={'Authorization': user_token}, json=product))

    # then
    assert response.status_code == 409


def test_list_products(user_token):
    # given
    add_product(user_token, some_product('P1', 1))
    add_product(user_token, some_product('P2', 2))

    # when
    response = (app.test_client()
                .get("/store/products/", headers={'Authorization': user_token}))

    # then
    assert response.status_code == 200
    body = json.loads(response.data.decode('utf-8'))
    assert_that(body).extracting('name', sort='name').contains_only('P1', 'P2')
    assert_that(body).extracting('quantity', sort='name').contains_only(1, 2)
    assert_that(body).extracting('product_id').is_not_empty()


@pytest.mark.skip(reason="can't test until multiple houses can be created")
def test_user_lists_only_own_home_products(user_tokens):
    # given
    user1_token, user2_token = user_tokens
    add_product(user1_token, some_product('Product', 1))
    add_product(user2_token, some_product('Product', 2))

    # when
    _, body = list_products(user2_token)

    # then
    assert len(body) == 1
    assert body[0]['name'] == 'Product'
    assert body[0]['quantity'] == 2


def test_update_product(user_token):
    # given
    product = some_product('Product', 1)
    location = add_product(user_token, product)
    updated_product = some_product('Updated name', 999)

    # when
    response = (app.test_client()
                .put(location, headers={'Authorization': user_token}, json=updated_product))

    # then
    assert response.status_code == 200
    _, body = list_products(user_token)
    assert len(body) == 1
    assert_that(body[0]).is_equal_to(updated_product, ignore='product_id')


# TODO: def test_deleting_product

def test_delete_product(user_token):
    product_location = add_product(user_token, some_product())

    status_code, products_in_database_before_deletion = list_products(user_token)
    assert len(products_in_database_before_deletion) == 1

    response = app.test_client().delete(product_location, headers={'Authorization': user_token})
    assert response.status_code == 200

    status_code, products_in_database_after_deletion = list_products(user_token)
    assert len(products_in_database_after_deletion) == 0


def test_delete_shopping_item(user_token):
    location = add_shopping_item(user_token, some_product())

    status_code, products_in_database_before_deletion = list_shopping_items(user_token)
    assert len(products_in_database_before_deletion) == 1

    response = app.test_client().delete(location, headers={'Authorization': user_token})
    assert response.status_code == 200

    status_code, products_in_database_after_deletion = list_products(user_token)
    assert len(products_in_database_after_deletion) == 0


def test_delete_product_fails_if_non_existing_id(user_token):
    add_product(user_token, some_product())
    status_code, products_in_database_before_deletion = list_products(user_token)
    assert len(products_in_database_before_deletion) == 1

    non_existing_id = '9797603a-6520-42f3-adba-c78988b8ff9f'
    deletion_response = app.test_client().delete(f'/store/products/{non_existing_id}',
                                                 headers={'Authorization': user_token})

    assert deletion_response.status_code == 404
    status_code, products_in_database_after_deletion = list_products(user_token)
    assert len(products_in_database_after_deletion) == 1


def test_delete_shoping_item_fails_if_non_existing_id(user_token):
    add_shopping_item(user_token, some_product())
    status_code, products_in_database_before_deletion = list_shopping_items(user_token)
    assert len(products_in_database_before_deletion) == 1

    non_existing_id = '9797603a-6520-42f3-adba-c78988b8ff9f'
    deletion_response = app.test_client().delete(f'/cart/items/{non_existing_id}',
                                                 headers={'Authorization': user_token})

    assert deletion_response.status_code == 404
    status_code, shopping_items_in_database_after_deletion = list_shopping_items(user_token)
    assert len(shopping_items_in_database_after_deletion) == 1


def test_adding_shopping_item(user_token):
    # given
    shopping_item = some_shopping_item()

    # when
    response = (app.test_client()
                .post("/cart/items/", headers={'Authorization': user_token}, json=shopping_item))

    # then
    assert response.status_code == 201
    location = response.headers['Location']
    assert location.startswith("/cart/items/")
    assert_that(location).matches(r'/cart/items/[0-9a-f]+')
    _, body = list_shopping_items(user_token)
    assert len(body) == 1
    assert body[0]['name'] == shopping_item['name']
    assert body[0]['quantity'] == shopping_item['quantity']


def test_update_shopping_item(user_token):
    # given
    product = some_shopping_item('Product', 1)
    location = add_shopping_item(user_token, product)
    updated_shopping_item = some_shopping_item('Updated name', 999)
    updated_shopping_item['checkout'] = False

    # when
    response = (app.test_client()
                .put(location, headers={'Authorization': user_token}, json=updated_shopping_item))

    # then
    assert response.status_code == 200
    _, body = list_shopping_items(user_token)
    assert len(body) == 1
    assert_that(body[0]).is_equal_to(updated_shopping_item, ignore=['product_id'])


def test_list_shopping_items(user_token):
    # given
    shopping_item = some_shopping_item('Name', 9)
    add_shopping_item(user_token, shopping_item)

    # when
    response = (app.test_client()
                .get("/cart/items/", headers={'Authorization': user_token}))

    # then
    assert response.status_code == 200
    body = json.loads(response.data.decode('utf-8'))
    print(body)
    assert len(body) == 1
    assert body[0]['name'] == shopping_item['name']
    assert body[0]['quantity'] == shopping_item['quantity']
    assert body[0]['checkout'] == False


@pytest.mark.skip(reason="can't test until multiple houses can be created")
def test_user_lists_only_own_shopping_items(user_tokens):
    # given
    user1_token, user2_token = user_tokens
    add_shopping_item(user1_token, some_shopping_item('Product', 1))
    add_shopping_item(user2_token, some_shopping_item('Product', 2))

    # when
    _, body = list_shopping_items(user1_token)

    # then
    assert len(body) == 1
    assert body[0]['name'] == 'Product'
    assert body[0]['quantity'] == 1


def test_adding_missing_products_to_empty_shopping_list(user_token):
    # given
    missing_product_1 = some_product(name='missing_product_1', quantity=0)
    missing_product_2 = some_product(name='missing_product_2', quantity=0)
    add_product(user_token, missing_product_1)
    add_product(user_token, some_product(quantity=20))
    add_product(user_token, some_product(quantity=1))
    add_product(user_token, missing_product_2)
    _, products_body = list_products(user_token)
    assert len(products_body) == 4

    # when
    response = (app.test_client()
                .post("/cart/items/shoppinglist", headers={'Authorization': user_token}))

    # then
    assert response.status_code == 201
    _, body = list_shopping_items(user_token)
    print(body)
    assert len(body) == 2
    assert body[0]['name'] == 'missing_product_1'
    assert body[0]['quantity'] == 1
    assert body[1]['name'] == 'missing_product_2'
    assert body[1]['quantity'] == 1


def test_adding_missing_products_to_prefilled_shopping_list(user_token):
    # given
    some_item = some_shopping_item()
    other_shopping_item = some_shopping_item()
    add_shopping_item(user_token, some_item)
    add_shopping_item(user_token, other_shopping_item)
    _, items_body = list_shopping_items(user_token)
    assert len(items_body) == 2

    # and
    missing_product_with_same_name = some_product(name=some_item['name'], quantity=0)
    other_missing_product = some_product(quantity=0)
    add_product(user_token, missing_product_with_same_name)
    add_product(user_token, other_missing_product)
    _, products_body = list_products(user_token)
    assert len(products_body) == 2

    expected_shopping_items = [
        (some_item['name'], some_item['quantity'], False),
        (other_shopping_item['name'], other_shopping_item['quantity'], False),
        (other_missing_product['name'], 1, False)
    ]

    # when
    response = (app.test_client()
                .post("/cart/items/shoppinglist", headers={'Authorization': user_token}))

    # then
    assert response.status_code == 201
    _, body = list_shopping_items(user_token)
    assert len(body) == 3
    shopping_items = list(map(lambda b: (b['name'], b['quantity'], b['checkout']), body))

    assert all(item in expected_shopping_items for item in shopping_items)


def test_adding_not_bought_shopping_items_to_products(user_token):
    # given
    add_shopping_item(user_token, some_shopping_item(quantity=random_number(1, 100)))

    # when
    response = (app.test_client()
                .post("/store/products/delivery/", headers={'Authorization': user_token}))

    # then
    assert response.status_code == 200
    status, products = list_products(user_token)
    assert len(products) == 0


def test_adding_bought_shopping_items_to_products(user_token):
    # given
    product = some_product()
    add_product(user_token, product)

    # and
    new_bought_item = some_shopping_item(quantity=random_number(1, 100))
    existing_bought_item = some_shopping_item(name=product['name'], quantity=random_number(1, 100))
    new_bought_item_location = add_shopping_item(user_token, new_bought_item)
    existing_bought_item_location = add_shopping_item(user_token, existing_bought_item)

    # and marked as bought
    new_bought_item['checkout'] = existing_bought_item['checkout'] = True
    update_resource(user_token, new_bought_item_location, new_bought_item)
    update_resource(user_token, existing_bought_item_location, existing_bought_item)

    # when
    response = (app.test_client()
                .post("/store/products/delivery/", headers={'Authorization': user_token}))

    # then
    assert response.status_code == 200
    status, products = list_products(user_token)
    assert len(products) == 2
    existing_product = next(filter(lambda p: p['name'] == product['name'], products))
    new_product = next(filter(lambda p: p['name'] == new_bought_item['name'], products))
    assert existing_product['quantity'] == product['quantity'] + existing_bought_item['quantity']
    assert new_product['quantity'] == new_bought_item['quantity']


def add_product(token, product):
    response = (app.test_client()
                .post("/store/products/", headers={'Authorization': token}, json=product))
    assert response.status_code == 201
    return response.headers['Location']


def add_home(token, home):
    response = (app.test_client()
                .post("/homes", headers={'Authorization': token}, json=home))
    assert response.status_code == 201
    return response.headers['Location']


def update_resource(token, location, resource):
    response = (app.test_client()
                .put(location, headers={'Authorization': token}, json=resource))
    assert response.status_code == 200
    return response


def add_shopping_item(token, shopping_item):
    response = (app.test_client()
                .post("/cart/items/", headers={'Authorization': token}, json=shopping_item))
    assert response.status_code == 201
    return response.headers['Location']


def list_products(token):
    return list_resources(token, "/store/products/")


def list_shopping_items(token):
    return list_resources(token, "/cart/items/")


def list_resources(token, resource_path):
    response = (app.test_client()
                .get(resource_path, headers={'Authorization': token}))
    body = json.loads(response.data.decode('utf-8'))
    assert response.status_code == 200
    return response.status_code, body
