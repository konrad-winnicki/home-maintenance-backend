import os

import pytest

from request_guard import request_guard
from errors import BadRequest


@pytest.fixture(autouse=True)
def set_app_profile():
    os.environ['APP_PROFILE'] = 'test'


def test_request_guard_returns_true():
    request = {'name': 'home1', 'name2': 'home2'}
    expected_key_types = {'name': str, 'name2': str}
    try:
        request_guard(request, expected_key_types)
    except ValueError:
        pytest.fail("Unexpected ValueError raised")


def test_request_guard_raise_error_if_request_keys_and_expected_keys_differs():
    request = {'name': 'home1', 'name2': 'home2', 'name3': 'home3'}
    expected_key_types = {'name': str, 'name2': str}
    with pytest.raises(BadRequest) as error_info:
        request_guard(request, expected_key_types)
    assert str(error_info.value) == "Request should contain object {'name': <class 'str'>, 'name2': <class 'str'>}"

def test_request_guard_returns_false_if_types_not_match():
    request = {'quantity': '1', 'product_name': 'milk'}
    expected_key_types = {'product_name': str, 'quantity': int}
    with pytest.raises(BadRequest) as error_info:
        request_guard(request, expected_key_types)
    assert str(error_info.value) == "Request should contain object {'product_name': <class 'str'>, 'quantity': <class 'int'>}"