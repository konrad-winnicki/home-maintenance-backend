from db import execute_fetch_all, execute_sql_query, execute_fetch
from errors import ResourceNotExists


def insert_shopping_list_item(item_id, name, quantity, user_context):
    _, home_id = user_context
    is_bought = False
    query_sql = """INSERT INTO shopping_list_items 
                    (id, name, home_id, quantity, is_bought)
                    VALUES (%s, %s, %s, %s, %s)"""
    execute_sql_query(query_sql, [item_id, name, home_id, quantity, is_bought])


def insert_user(user_id, user_account_number):
    query_sql = "INSERT INTO users VALUES (%s, %s)"
    execute_sql_query(query_sql, [user_id, user_account_number])
    return user_id


def insert_home(home_id, name):
    query_sql = "INSERT INTO homes (id, name) VALUES (%s, %s)"
    execute_sql_query(query_sql, [home_id, name])


def get_homes(user_id):
    query_sql = 'select id, name from homes h, home_members m where h.id = m.home_id and m.user_id=%s order by name'
    return execute_fetch_all(query_sql, [user_id],
                             lambda row: {"id": row["id"], "name": row["name"]})


def insert_home_member(home_id, user_id):
    query_sql = "INSERT INTO home_members (home_id, user_id) VALUES (%s, %s)"
    execute_sql_query(query_sql, [home_id, user_id])


def insert_product(product_id, name, quantity, user_context):
    _, home_id = user_context
    query_sql = "INSERT INTO products (id, name, quantity, home_id) VALUES (%s, %s, %s, %s)"
    execute_sql_query(query_sql, [product_id, name, quantity, home_id])


def get_products(user_context):
    _, home_id = user_context
    query_sql = 'select id, name, quantity from products where home_id=%s order by products.name'
    return execute_fetch_all(query_sql, [home_id],
                             lambda row: {"product_id": row["id"], "quantity": row["quantity"],
                                          "name": row["name"]})


def get_missing_products(user_context):
    _, home_id = user_context
    query_sql = 'select id, name from products where home_id=%s and quantity = 0'
    return execute_fetch_all(query_sql, [home_id],
                             lambda row: {"product_id": row["id"], "name": row["name"]})


def get_shopping_list_items(user_context):
    _, home_id = user_context
    query_sql = "select id, name, quantity, is_bought from shopping_list_items where home_id=%s order by name"
    return execute_fetch_all(query_sql, [home_id],
                             lambda row: {"product_id": row["id"], "quantity": row["quantity"], "name": row["name"],
                                          "is_bought": row["is_bought"]})


def get_shopping_item_by_id(item_id, user_context):
    _, home_id = user_context
    query_sql = "select * from shopping_list_items where id=%s and home_id=%s"
    fetch_result = execute_fetch(query_sql, [item_id, home_id])
    if fetch_result:
        return {"name": fetch_result.get('name'), "quantity": fetch_result.get('quantity')}
    return None


def get_bought_shopping_items(user_context):
    _, home_id = user_context
    query_sql = "select id, name, quantity from shopping_list_items where home_id=%s and is_bought = true"
    return execute_fetch_all(query_sql, [home_id],
                             lambda row: {"id": row["id"], "quantity": row["quantity"], "name": row["name"]})


def get_user_id(user_account_number):
    query_sql = "select * from users where user_account_number=%s"
    fetch_result = execute_fetch(query_sql, [user_account_number])
    if fetch_result:
        user_id = fetch_result.get("id")
        return user_id


def get_product_by_name(name, user_context):
    _, home_id = user_context
    query_sql = "select * from products where name=%s and home_id=%s"
    fetch_result = execute_fetch(query_sql, [name, home_id])
    if fetch_result:
        return {"id": fetch_result.get('id'), "quantity": fetch_result.get('quantity')}


def get_product_by_id(product_id, user_context):
    _, home_id = user_context
    query_sql = "select * from products where id=%s and home_id=%s"
    fetch_result = execute_fetch(query_sql, [product_id, home_id])
    if fetch_result:
        return {"name": fetch_result.get('name'), "quantity": fetch_result.get('quantity')}
    return None


def delete_product(product_id, user_context):
    _, home_id = user_context
    exists_product = get_product_by_id(product_id, user_context)
    if not exists_product:
        raise ResourceNotExists

    query_sql = "DELETE FROM products WHERE id=%s and home_id=%s"
    execute_sql_query(query_sql, [product_id, home_id])


def delete_user_from_home(user_context):
    user_id, home_id = user_context
    #TODO: check if home and user exists
   # exists_product = get_product_by_id(product_id, user_context)
   # if not exists_product:
        #raise ResourceNotExists
    query_sql = "DELETE FROM home_members WHERE home_id=%s and user_id=%s"
    execute_sql_query(query_sql, [home_id, user_id])



def delete_shopping_list_item(item_id, user_context):
    _, home_id = user_context
    exists_shopping_item = get_shopping_item_by_id(item_id, user_context)
    if not exists_shopping_item:
        raise ResourceNotExists

    query_sql = "DELETE FROM shopping_list_items WHERE id=%s and home_id=%s"
    execute_sql_query(query_sql, [item_id, home_id])


def update_product(product_id, name, quantity, user_context):
    _, home_id = user_context
    query_sql = "update products SET name=%s, quantity=%s where id=%s and home_id=%s"
    execute_sql_query(query_sql, [name, quantity, product_id, home_id])


def update_shopping_list_item(item_id, name, quantity, is_bought, user_context):
    _, home_id = user_context
    query_sql = "update shopping_list_items SET name=%s, quantity=%s, is_bought=%s where id=%s and home_id=%s"
    execute_sql_query(query_sql, [name, quantity, is_bought, item_id, home_id])
