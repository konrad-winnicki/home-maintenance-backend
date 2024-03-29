import uuid

from src.errors import ResourceAlreadyExists, ResourceNotExists
from src.persistence import get_product_by_name, insert_product, delete_shopping_list_item, \
    insert_shopping_list_item, update_product, \
    get_missing_products, get_bought_shopping_items, insert_home, insert_home_member, user_membership, \
    get_barcode_details, insert_barcode, update_shopping_list_item, get_shopping_item_by_name, get_home_by_name


def generate_unique_id():
    return uuid.uuid4().__str__()


def check_membership(home_id, user_id):
    if not user_membership(home_id, user_id):
        raise ResourceNotExists


def add_home(name, user_id):
    existing_home = get_home_by_name(name, user_id)
    if existing_home:
        raise ResourceAlreadyExists
    home_id = generate_unique_id()
    insert_home(home_id, name)
    insert_home_member(home_id, user_id)
    return home_id


def assign_user_to_home(home_id, user_id):
    try:
        insert_home_member(home_id, user_id)
        # TODO:
        # somebody is already a member of this house - zrobione
        # home not exists
        # user not exists
    except ResourceAlreadyExists:
        raise ResourceAlreadyExists
    except Exception as e:
        print("Couldn't add home member: " + e)
        raise ResourceNotExists


def add_bought_shopping_items(user_context):
    bought_items = get_bought_shopping_items(user_context)
    for item in bought_items:
        item_id = item.get('id')
        quantity = item.get('quantity')
        name = item.get('name')
        category = item.get('category')
        # TODO: we should get Product object
        existing_product = get_product_by_name(name, user_context)
        if existing_product is None:
            insert_product(item_id, name, quantity, category, user_context)
        else:
            product_id = existing_product.get('id')
            total_quantity = quantity + existing_product.get('quantity')
            update_product(product_id, name, total_quantity,category, user_context)
        delete_shopping_list_item(item_id, user_context)
    return "Products added to store"


def add_shopping_list_item(name, quantity, category, user_context):
    try:
        item_id = generate_unique_id()
        insert_shopping_list_item(item_id, name, quantity, category, user_context)

    except ResourceAlreadyExists:
        raise ResourceAlreadyExists
    return item_id


def add_product(name, quantity, category, user_context):
    try:
        product_id = generate_unique_id()
        insert_product(product_id, name, quantity, category, user_context)

    except ResourceAlreadyExists:
        raise ResourceAlreadyExists
    return product_id

def add_barcode(name, barcode, category, user_context):
    try:
        barcode_id = generate_unique_id()
        insert_barcode(barcode_id, name, barcode,category, user_context)
    except ResourceAlreadyExists:
        raise ResourceAlreadyExists
    return barcode_id




def modify_store(name, category, user_context):
    product = get_product_by_name(name, user_context)
    if product:
        id = product.get("id")
        quantity = product.get('quantity') + 1
        category = product.get('category')
        update_product(id, name, quantity, category, user_context)
        return {'response': 'updated', 'name': name, 'productId': id, 'quantity': quantity, 'category': category}
    product_id = generate_unique_id()
    quantity = 1
    insert_product(product_id, name, quantity, category, user_context)
    return {'response': 'added', 'name': name, 'productId': product_id, 'quantity': quantity, 'category': category}



def modify_store_by_barcode (barcode, user_context):
    details = get_barcode_details(barcode, user_context)

    if not details:
        raise ResourceNotExists
    name = details.get('name')
    category = details.get('category')
    return modify_store(name, category, user_context)


def modify_shopings(name, category, user_context):
    shopping_item = get_shopping_item_by_name(name, user_context)
    print('modify', shopping_item)
    if shopping_item:
        id = shopping_item.get("id")
        quantity = shopping_item.get('quantity')
        name = shopping_item.get('name')
        is_bought = True
        update_shopping_list_item(id, name, quantity, is_bought, user_context)
        return {'response': 'updated', 'name': name}

    shopping_id = generate_unique_id()
    quantity = 1
    insert_shopping_list_item(shopping_id, name, quantity, category, user_context)
    return {'response': 'added', 'name': name}


def modify_shopings_by_barcode (barcode, user_context):
    details = get_barcode_details(barcode, user_context)
    if not details:
        raise ResourceNotExists
    name = details.get('name')
    category = details.get('category')
    return modify_shopings(name, category, user_context)


def add_missing_products_to_shopping_list(user_context):
    missing_products = get_missing_products(user_context)
    for product in missing_products:
        name = product.get('name')
        category = product.get('category')
        quantity = 1
        try:
            item_id = generate_unique_id()
            insert_shopping_list_item(item_id, name, quantity,category, user_context)
        except ResourceAlreadyExists:
            continue
    return "Products added to shopping list"
