import uuid

from errors import ProductAlreadyExists
from persistence import get_product_id_by_name, replace_product_in_store_positions, change_product_name, \
    change_product_name_in_shopping_list, change_checkbox_status_in_database, check_if_product_id_in_products, \
    insert_product, delete_product_from_shopping_list, \
    insert_product_to_shopping_list, insert_product_with_name, insert_product_to_store_positions, insert_barcode, \
    get_quantity_by_id, increase_product_quantity_in_products, get_product_id_for_barcode



def generate_unique_id():
    return uuid.uuid4().__str__()


def change_name(product_id, new_name, user_id):
    maybe_existing_product_id = get_product_id_by_name(new_name, user_id)
    if maybe_existing_product_id:
        replace_product_in_store_positions(product_id, maybe_existing_product_id, user_id)
    else:
        change_product_name(product_id, new_name, user_id)
    return "Product name changed"


def change_name_in_shopping_list(product_id, new_name, user_id):
    maybe_existing_product_id = get_product_id_by_name(new_name, user_id)
    if maybe_existing_product_id:
        replace_product_in_store_positions(product_id, maybe_existing_product_id, user_id)
    else:
        change_product_name_in_shopping_list(product_id, new_name, user_id)
    return "Product name changed"


def change_checkbox_status(product_id, checkbox_status, user_id):
    change_checkbox_status_in_database(product_id, checkbox_status, user_id)
    return "Checkbox status changed"


def add_product_from_shopping_list(product_list, user_id):
    for item in product_list:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        name = item.get('name')
        if check_if_product_id_in_products(product_id, user_id) is None:
            insert_product(product_id, name, user_id)
        add_product_to_store_positions(product_id, quantity, user_id)
        delete_product_from_shopping_list(product_id, user_id)
    return "Products added to store"


def add_product_with_name_to_cart(name, quantity, user_id):
    existing_product_id = get_product_id_by_name(name, user_id)
    try:
        if existing_product_id:
            product_id = existing_product_id
        else:
            product_id = generate_unique_id()
        insert_product_to_shopping_list(product_id, name, quantity, user_id)

    except ProductAlreadyExists:
        raise ProductAlreadyExists
    return "Product added to database"


def add_product(name, quantity, user_id):
    try:
        product_id = generate_unique_id()
        insert_product(product_id, name, quantity, user_id)

    except ProductAlreadyExists:
        raise ProductAlreadyExists
    return product_id


def add_product_with_barcode_and_name(barcode, name, user_id):
    existing_product_id = get_product_id_by_name(name, user_id)
    if existing_product_id:
        product_id = existing_product_id
    else:
        product_id = generate_unique_id()
        insert_product_with_name(product_id, name, user_id)

    insert_barcode(barcode, product_id)  # what if barcode already exists?
    add_product_to_store_positions(product_id, 1, user_id)
    return "Product added to database", 201


def add_product_to_store_positions(product_id, quantity, user_id):
    try:
        insert_product_to_store_positions(product_id, quantity, user_id)
    except ProductAlreadyExists:
        existing_quantity = get_quantity_by_id(product_id, user_id)
        increase_product_quantity_in_products(product_id, existing_quantity + quantity, user_id)


def add_product_with_barcode(barcode, user_id):
    existing_product_id = get_product_id_for_barcode(barcode, user_id)
    if not existing_product_id:
        return "Barcode not found and name not given", 404
    add_product_to_store_positions(existing_product_id, 1, user_id)
    return "Product added to database", 201


def add_finished_products_to_shopping_list(product_list, user_id):
    for item in product_list:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        name = item.get('name')
        try:
            insert_product_to_shopping_list(product_id, name, quantity, user_id)
        except ProductAlreadyExists:
            continue
    return "Products added to shopping list"
