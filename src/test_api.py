import json

from api import app
from src.session import create_session


def test_that_unauthenticated_gets_401():
    response = app.test_client().get("/store/products/")
    assert response.status_code == 401


def jwt_token_for_user(username):
    create_session()
    return "jwt-token-for" + username


def test_listing_products():
    jwt_token = jwt_token_for_user('mafalda')
    response = (app.test_client()
                .get("/store/products/", headers={'Authorization': jwt_token}))
    print(response.data.decode('utf-8'))
    assert response.status_code == 200


def test_get_all_products():
    response = app.test_client().get("/store/products/")
    res = json.loads(response.data.decode('utf-8')).get("products")
    assert type(res[0]) is dict
    assert res[0]['name'] == 'Milk'
