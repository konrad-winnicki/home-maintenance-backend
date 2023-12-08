import json

import pytest

from session import create_session
from services import generate_unique_id
from src.api import app
from src.db import execute_sql_query
from src.persistence import insert_user, get_user_id


def delete_all_table_contents():
    tables = ["users", "products", "shopping_list_items"]
    list(map(lambda table: execute_sql_query("DELETE FROM " + table + ";", []), tables))


@pytest.fixture(autouse=True)
def prepare_users():
    delete_all_table_contents()
    insert_user(generate_unique_id(), 'mafalda')


def jwt_token_for_user(username):
    user_id = get_user_id(username)
    return create_session(user_id)


def test_that_unauthenticated_gets_401():
    response = app.test_client().get("/store/products/")
    assert response.status_code == 401


def test_listing_products():
    jwt_token = jwt_token_for_user('mafalda')
    response = (app.test_client()
                .get("/store/products/", headers={'Authorization': jwt_token}))
    print(response.data.decode('utf-8'))
    assert response.status_code == 200


def test_adding_products():
    jwt_token = jwt_token_for_user('mafalda')
    response1 = (app.test_client()
                 .post("/store/products/", headers={'Authorization': jwt_token},
                       json={'name': 'Milk', 'quantity': 2}))
    assert response1.status_code == 201
    response2 = (app.test_client()
                 .post("/store/products/", headers={'Authorization': jwt_token},
                       json={'name': 'Bread', 'quantity': 1}))
    assert response2.status_code == 201

    listing_response = list_products(jwt_token)

    body = json.loads(listing_response.data.decode('utf-8'))
    assert len(body) == 2
    print(body)
    assert body[0]['name'] == 'Bread'
    assert body[0]['quantity'] == 1
    assert body[1]['name'] == 'Milk'
    assert body[1]['quantity'] == 2


def add_product(jwt_token, product):
    return (app.test_client()
            .post("/store/products/", headers={'Authorization': jwt_token}, json=product))


def test_get_all_products():
    jwt_token = jwt_token_for_user('mafalda')
    add_product(jwt_token, {'name': 'P1', 'quantity': 1})
    add_product(jwt_token, {'name': 'P2', 'quantity': 2})
    response = (app.test_client()
                .get("/store/products/", headers={'Authorization': jwt_token}))
    body = json.loads(response.data.decode('utf-8'))
    assert len(body) == 2
    print(body)
    assert body[0]['name'] == 'P1'
    assert body[0]['quantity'] == 1
    assert len(body[0]['product_id']) > 0
    assert body[1]['name'] == 'P2'
    assert body[1]['quantity'] == 2
    assert len(body[1]['product_id']) > 0


def list_products(jwt_token):
    return (app.test_client()
            .get("/store/products/", headers={'Authorization': jwt_token}))
