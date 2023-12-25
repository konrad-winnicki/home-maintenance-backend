from errors import BadRequest


def request_guard(request_body, expected_attributes_types):
    if not request_body.keys() == expected_attributes_types.keys():
        raise BadRequest(expected_attributes_types)

    for key, value in request_body.items():
        key_type = expected_attributes_types.get(key)
        if not isinstance(value, key_type):
            raise BadRequest(expected_attributes_types)


