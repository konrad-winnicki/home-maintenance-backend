import json
import os
import random
import string

import pytest
from assertpy import assert_that

from src.api import app
from src.db import execute_sql_query
from src.db_schema import create_tables
from src.persistence import insert_user
from src.services import generate_unique_id
from src.session import create_session


def delete_all_table_contents():
    tables = ["users", "products", "shopping_list_items", "homes", "home_members"]
    list(map(lambda table: execute_sql_query("DELETE FROM " + table + ";", []), tables))
    add_test_home()


def add_test_home():
    execute_sql_query("INSERT INTO homes (id, name) VALUES (%s, %s)",
                      ['b9e3c6fc-bc97-4790-9f46-623ce14b25f1', 'default home'])


# TODO: create db schema before all tests

@pytest.fixture(scope='session', autouse=True)
def create_db_schema():
    create_tables()


@pytest.fixture(autouse=True)
def clean_database():
    delete_all_table_contents()


@pytest.fixture(autouse=True)
def set_app_profile():
    os.environ['APP_PROFILE'] = 'test'


@pytest.fixture
def user_tokens():
    user_id1 = insert_user(generate_unique_id(), 'user1', 'user1@domain.test')
    user_id2 = insert_user(generate_unique_id(), 'user2', 'user2@domain.test')
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
    response = app.test_client().get("/homes")
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


def test_home_membership(user_token):
    # given
    home_location = add_home(user_token, some_home())
    non_existing_home_id = 'b9e3c6fc-bc97-4790-9f46-623ce14b2fff'

    products_endpoint_with_existing_home_id = f'{home_location}/store/products'
    products_endpoint_with_non_existing_home_id = f'homes/{non_existing_home_id}/store/products'

    # when
    response1 = (app.test_client()
                 .post(products_endpoint_with_existing_home_id, headers={'Authorization': user_token},
                       json=some_product('Milk', 2)))
    response2 = (app.test_client()
                 .post(products_endpoint_with_non_existing_home_id, headers={'Authorization': user_token},
                      json=some_product('Bread', 1)))
#
    # then

    assert response1.status_code == 201
    assert response2.status_code == 404
    assert response2.json == {'response': 'resource does not exist'}





def test_adding_products(user_token):
    # given
    home_location = add_home(user_token, some_home())
    #print('dddddddd', home_location)
    products_endpoint = f'{home_location}/store/products'

    # when
    response1 = (app.test_client()
                 .post(products_endpoint, headers={'Authorization': user_token},
                       json=some_product('Milk', 2)))
    response2 = (app.test_client()
                 .post(products_endpoint, headers={'Authorization': user_token},
                       json=some_product('Bread', 1)))

    # then
    assert response1.status_code == 201
    assert response2.status_code == 201
    _, body = list_products(user_token, home_location)
    assert_that(body).extracting('name', sort='name').contains_only('Bread', 'Milk')
    assert_that(body).extracting('quantity', sort='name').contains_only(1, 2)
    assert_that(body).extracting('product_id').is_not_empty()





def test_adding_product_with_same_name_fails(user_token):
    # given
    home_location = add_home(user_token, some_home())
    product = some_product()
    r = add_product(user_token, home_location, product)
    print('first r', r)
    # when
    response = (app.test_client()
                .post(f'{home_location}/store/products', headers={'Authorization': user_token}, json=product))

    # then
    print('response', response)
    assert response.status_code == 409


def test_list_products(user_token):
    # given
    home_location = add_home(user_token, some_home())
    add_product(user_token, home_location, some_product('P1', 1))
    add_product(user_token, home_location, some_product('P2', 2))

    # when
    response = (app.test_client()
                .get(f'{home_location}/store/products', headers={'Authorization': user_token}))

    # then
    assert response.status_code == 200
    body = json.loads(response.data.decode('utf-8'))
    assert_that(body).extracting('name', sort='name').contains_only('P1', 'P2')
    assert_that(body).extracting('quantity', sort='name').contains_only(1, 2)
    assert_that(body).extracting('product_id').is_not_empty()


def test_user_lists_only_own_home_products(user_tokens):
    # given
    user1_token, user2_token = user_tokens
    home1 = add_home(user1_token, some_home())
    home2 = add_home(user2_token, some_home())
    add_product(user1_token, home1, some_product('Product', 1))
    add_product(user2_token, home2, some_product('Product', 2))

    # when
    _, body = list_products(user2_token, home2)

    # then
    assert len(body) == 1
    assert body[0]['name'] == 'Product'
    assert body[0]['quantity'] == 2


def test_update_product(user_token):
    # given
    home_location = add_home(user_token, some_home())
    product = some_product('Product', 1)
    location = add_product(user_token, home_location, product)
    updated_product = some_product('Updated name', 999)

    # when
    response = (app.test_client()
                .put(location, headers={'Authorization': user_token}, json=updated_product))

    # then
    assert response.status_code == 200
    _, body = list_products(user_token, home_location)
    assert len(body) == 1
    assert_that(body[0]).is_equal_to(updated_product, ignore='product_id')


def test_delete_product(user_token):
    home_location = add_home(user_token, some_home())
    product_location = add_product(user_token, home_location, some_product())

    status_code, products_in_database_before_deletion = list_products(user_token, home_location)
    assert len(products_in_database_before_deletion) == 1

    response = app.test_client().delete(product_location, headers={'Authorization': user_token})
    assert response.status_code == 200

    status_code, products_in_database_after_deletion = list_products(user_token, home_location)
    assert len(products_in_database_after_deletion) == 0


def test_delete_shopping_item(user_token):
    home_location = add_home(user_token, some_home())
    location = add_shopping_item(user_token, home_location, some_product())

    status_code, products_in_database_before_deletion = list_shopping_items(user_token, home_location)
    assert len(products_in_database_before_deletion) == 1

    response = app.test_client().delete(location, headers={'Authorization': user_token})
    assert response.status_code == 200

    status_code, products_in_database_after_deletion = list_products(user_token, home_location)
    assert len(products_in_database_after_deletion) == 0


def test_delete_product_fails_if_non_existing_id(user_token):
    home_location = add_home(user_token, some_home())
    add_product(user_token, home_location, some_product())
    status_code, products_in_database_before_deletion = list_products(user_token, home_location)
    assert len(products_in_database_before_deletion) == 1

    non_existing_id = '9797603a-6520-42f3-adba-c78988b8ff9f'
    deletion_response = app.test_client().delete(f'{home_location}/store/products/{non_existing_id}',
                                                 headers={'Authorization': user_token})

    assert deletion_response.status_code == 404
    status_code, products_in_database_after_deletion = list_products(user_token, home_location)
    assert len(products_in_database_after_deletion) == 1


def test_delete_shopping_item_fails_if_non_existing_id(user_token):
    home_location = add_home(user_token, some_home())
    add_shopping_item(user_token, home_location, some_product())
    status_code, products_in_database_before_deletion = list_shopping_items(user_token, home_location)
    assert len(products_in_database_before_deletion) == 1

    non_existing_id = '9797603a-6520-42f3-adba-c78988b8ff9f'
    deletion_response = app.test_client().delete(f'{home_location}/cart/items/{non_existing_id}',
                                                 headers={'Authorization': user_token})

    assert deletion_response.status_code == 404
    status_code, shopping_items_in_database_after_deletion = list_shopping_items(user_token, home_location)
    assert len(shopping_items_in_database_after_deletion) == 1


def test_adding_shopping_item(user_token):
    # given
    home_location = add_home(user_token, some_home())
    shopping_item = some_shopping_item()

    # when
    response = (app.test_client()
                .post(f'{home_location}/cart/items', headers={'Authorization': user_token}, json=shopping_item))

    # then
    assert response.status_code == 201
    location = response.headers['Location']
    assert_that(location).matches(fr'^{home_location}/cart/items/[0-9a-f]+')
    _, body = list_shopping_items(user_token, home_location)
    assert len(body) == 1
    assert body[0]['name'] == shopping_item['name']
    assert body[0]['quantity'] == shopping_item['quantity']


def test_update_shopping_item(user_token):
    # given
    home_location = add_home(user_token, some_home())
    product = some_shopping_item('Product', 1)
    product_location = add_shopping_item(user_token, home_location, product)
    updated_shopping_item = some_shopping_item('Updated name', 999)
    updated_shopping_item['is_bought'] = False

    # when
    response = (app.test_client()
                .put(product_location, headers={'Authorization': user_token}, json=updated_shopping_item))

    # then
    assert response.status_code == 200
    _, body = list_shopping_items(user_token, home_location)
    assert len(body) == 1
    assert_that(body[0]).is_equal_to(updated_shopping_item, ignore=['product_id'])


def test_list_shopping_items(user_token):
    # given
    home_location = add_home(user_token, some_home())
    shopping_item = some_shopping_item('Name', 9)
    add_shopping_item(user_token, home_location, shopping_item)

    # when
    response = (app.test_client()
                .get(f'{home_location}/cart/items', headers={'Authorization': user_token}))

    # then
    assert response.status_code == 200
    body = json.loads(response.data.decode('utf-8'))
    assert len(body) == 1
    assert body[0]['name'] == shopping_item['name']
    assert body[0]['quantity'] == shopping_item['quantity']
    assert body[0]['is_bought'] == False


def test_user_lists_only_own_shopping_items(user_tokens):
    # given
    user1_token, user2_token = user_tokens
    home1 = add_home(user1_token, some_home())
    home2 = add_home(user2_token, some_home())
    add_shopping_item(user1_token, home1, some_shopping_item('Product', 1))
    add_shopping_item(user2_token, home2, some_shopping_item('Product', 2))

    # when
    _, body = list_shopping_items(user2_token, home2)

    # then
    assert len(body) == 1
    assert body[0]['name'] == 'Product'
    assert body[0]['quantity'] == 2


def test_adding_missing_products_to_empty_shopping_list(user_token):
    # given
    home_location = add_home(user_token, some_home())
    missing_product_1 = some_product(name='missing_product_1', quantity=0)
    missing_product_2 = some_product(name='missing_product_2', quantity=0)
    products = [missing_product_1, some_product(quantity=20), some_product(quantity=1), missing_product_2]
    list(map(lambda p: add_product(user_token, home_location, p), products))
    _, products_body = list_products(user_token, home_location)
    assert len(products_body) == 4

    # when
    response = (app.test_client()
                .post(f'{home_location}/cart/items/shoppinglist', headers={'Authorization': user_token}))

    # then
    assert response.status_code == 201
    _, body = list_shopping_items(user_token, home_location)
    assert len(body) == 2
    assert body[0]['name'] == 'missing_product_1'
    assert body[0]['quantity'] == 1
    assert body[1]['name'] == 'missing_product_2'
    assert body[1]['quantity'] == 1


def test_adding_missing_products_to_prefilled_shopping_list(user_token):
    # given
    home_location = add_home(user_token, some_home())
    some_item = some_shopping_item()
    other_shopping_item = some_shopping_item()
    add_shopping_item(user_token, home_location, some_item)
    add_shopping_item(user_token, home_location, other_shopping_item)
    _, items_body = list_shopping_items(user_token, home_location)
    assert len(items_body) == 2

    # and
    missing_product_with_same_name = some_product(name=some_item['name'], quantity=0)
    other_missing_product = some_product(quantity=0)
    add_product(user_token, home_location, missing_product_with_same_name)
    add_product(user_token, home_location, other_missing_product)
    _, products_body = list_products(user_token, home_location)
    assert len(products_body) == 2

    expected_shopping_items = [
        (some_item['name'], some_item['quantity'], False),
        (other_shopping_item['name'], other_shopping_item['quantity'], False),
        (other_missing_product['name'], 1, False)
    ]

    # when
    response = (app.test_client()
                .post(f'{home_location}/cart/items/shoppinglist', headers={'Authorization': user_token}))

    # then
    assert response.status_code == 201
    _, body = list_shopping_items(user_token, home_location)
    assert len(body) == 3
    shopping_items = map(lambda i: (i['name'], i['quantity'], i['is_bought']), body)
    assert_that(shopping_items).is_subset_of(expected_shopping_items)


def test_adding_not_bought_shopping_items_to_products(user_token):
    # given
    home_location = add_home(user_token, some_home())
    add_shopping_item(user_token, home_location, some_shopping_item(quantity=random_number(1, 100)))

    # when
    response = (app.test_client()
                .post(f'{home_location}/store/products/delivery', headers={'Authorization': user_token}))

    # then
    assert response.status_code == 200
    status, products = list_products(user_token, home_location)
    assert len(products) == 0


def test_adding_bought_shopping_items_to_products(user_token):
    # given
    home_location = add_home(user_token, some_home())
    product = some_product()
    add_product(user_token, home_location, product)

    # and
    new_bought_item = some_shopping_item(quantity=random_number(1, 100))
    existing_bought_item = some_shopping_item(name=product['name'], quantity=random_number(1, 100))
    new_bought_item_location = add_shopping_item(user_token, home_location, new_bought_item)
    existing_bought_item_location = add_shopping_item(user_token, home_location, existing_bought_item)

    # and marked as bought
    new_bought_item['is_bought'] = existing_bought_item['is_bought'] = True
    update_resource(user_token, new_bought_item_location, new_bought_item)
    update_resource(user_token, existing_bought_item_location, existing_bought_item)

    # when
    response = (app.test_client()
                .post(f'{home_location}/store/products/delivery', headers={'Authorization': user_token}))

    # then
    assert response.status_code == 200
    status, products = list_products(user_token, home_location)
    assert len(products) == 2
    existing_product = next(filter(lambda p: p['name'] == product['name'], products))
    new_product = next(filter(lambda p: p['name'] == new_bought_item['name'], products))
    assert existing_product['quantity'] == product['quantity'] + existing_bought_item['quantity']
    assert new_product['quantity'] == new_bought_item['quantity']


def add_product(token, home_location, product):
    response = (app.test_client()
                .post(f'{home_location}/store/products', headers={'Authorization': token}, json=product))
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


def add_shopping_item(token, home_location, shopping_item):
    response = (app.test_client()
                .post(f'{home_location}/cart/items', headers={'Authorization': token}, json=shopping_item))
    assert response.status_code == 201
    return response.headers['Location']


def list_products(token, home_location):
    return list_resources(token, f'{home_location}/store/products')


def list_shopping_items(token, home_location):
    return list_resources(token, f'{home_location}/cart/items')


def list_resources(token, resource_path):
    response = (app.test_client()
                .get(resource_path, headers={'Authorization': token}))
    body = json.loads(response.data.decode('utf-8'))
    assert response.status_code == 200
    return response.status_code, body
