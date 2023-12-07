import json

from api import app


def test_get_all_products():
    response = app.test_client().get("/store/products/")
    res = json.loads(response.data.decode('utf-8')).get("products")
    assert type(res[0]) is dict
    assert res[0]['name'] == 'Milk'
