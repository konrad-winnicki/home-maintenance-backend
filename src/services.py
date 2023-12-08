import uuid

from errors import ResourceAlreadyExists
from persistence import get_bought_shopping_items
from persistence import get_product_by_name, insert_product, delete_shopping_list_item, \
    insert_shopping_list_item, update_product, \
    get_missing_products


def generate_unique_id():
    return uuid.uuid4().__str__()


def add_bought_shopping_items(user_id):
    bought_items = get_bought_shopping_items(user_id)
    for item in bought_items:
        item_id = item.get('id')
        quantity = item.get('quantity')
        name = item.get('name')

        # TODO: we should get Product object
        existing_product = get_product_by_name(name, user_id)
        if existing_product is None:
            insert_product(item_id, name, quantity, user_id)
        else:
            product_id = existing_product.get('id')
            total_quantity = quantity + existing_product.get('quantity')
            update_product(product_id, name, total_quantity, user_id)
        delete_shopping_list_item(item_id, user_id)
    return "Products added to store"


def add_shopping_list_item(name, quantity, user_id):
    try:
        item_id = generate_unique_id()
        insert_shopping_list_item(item_id, name, quantity, user_id)

    except ResourceAlreadyExists:
        raise ResourceAlreadyExists
    return item_id


def add_product(name, quantity, user_id):
    try:
        product_id = generate_unique_id()
        insert_product(product_id, name, quantity, user_id)

    except ResourceAlreadyExists:
        raise ResourceAlreadyExists
    return product_id


def add_missing_products_to_shopping_list(user_id):
    missing_products = get_missing_products(user_id)
    for product in missing_products:
        name = product.get('name')
        quantity = 1
        try:
            item_id = generate_unique_id()
            insert_shopping_list_item(item_id, name, quantity, user_id)
            print("dd")
        except ResourceAlreadyExists:
            continue
    return "Products added to shopping list"
