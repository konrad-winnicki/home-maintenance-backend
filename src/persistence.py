from db import execute_fetch_all, execute_sql_query, execute_fetch


def insert_shopping_list_item(item_id, name, quantity, user_id):
    is_bought = False
    query_sql = """INSERT INTO shopping_list_items 
                    (id, name, user_id, quantity, is_bought)
                    VALUES (%s, %s, %s, %s, %s)"""
    execute_sql_query(query_sql, [item_id, name, user_id, quantity, is_bought])


def insert_user(user_id, user_account_number):
    query_sql = "INSERT INTO users VALUES (%s, %s)"
    execute_sql_query(query_sql, [user_id, user_account_number])
    return user_id


def insert_product(product_id, name, quantity, user_id):
    query_sql = "INSERT INTO products (id, name, quantity, user_id) VALUES (%s, %s, %s, %s)"
    execute_sql_query(query_sql, [product_id, name, quantity, user_id])


def get_products(user_id):
    query_sql = 'select id, name, quantity from products where user_id=%s order by products.name'
    return execute_fetch_all(query_sql, [user_id],
                             lambda row: {"product_id": row["id"], "quantity": row["quantity"],
                                          "name": row["name"]})


def get_missing_products(user_id):
    query_sql = 'select id, name from products where user_id=%s and quantity = 0'
    return execute_fetch_all(query_sql, [user_id],
                             lambda row: {"product_id": row["id"], "name": row["name"]})


def get_shopping_list_items(user_id):
    query_sql = "select id, name, quantity, is_bought from shopping_list_items where user_id=%s order by name"
    return execute_fetch_all(query_sql, [user_id],
                             lambda row: {"product_id": row["id"], "quantity": row["quantity"], "name": row["name"],
                                          "checkout": row["is_bought"]})


def get_bought_shopping_items(user_id):
    query_sql = "select id, name, quantity from shopping_list_items where user_id=%s and is_bought = true"
    return execute_fetch_all(query_sql, [user_id],
                             lambda row: {"id": row["id"], "quantity": row["quantity"], "name": row["name"]})


def get_user_id(user_account_number):
    query_sql = "select * from users where user_account_number=%s"
    fetch_result = execute_fetch(query_sql, [user_account_number])
    if fetch_result:
        user_id = fetch_result.get("id")
        return user_id


def get_product_by_name(name, user_id):
    query_sql = "select * from products where name=%s and user_id=%s"
    fetch_result = execute_fetch(query_sql, [name, user_id])
    if fetch_result:
        return {"id": fetch_result.get('id'), "quantity": fetch_result.get('quantity')}


def delete_product(product_id, user_id):
    query_sql = "DELETE FROM products WHERE id=%s and user_id=%s"
    execute_sql_query(query_sql, [product_id, user_id])


def delete_shopping_list_item(item_id, user_id):
    query_sql = "DELETE FROM shopping_list_items WHERE id=%s and user_id=%s"
    execute_sql_query(query_sql, [item_id, user_id])


def update_product(product_id, name, quantity, user_id):
    query_sql = "update products SET name=%s, quantity=%s where id=%s and user_id=%s"
    execute_sql_query(query_sql, [name, quantity, product_id, user_id])


def update_shopping_list_item(item_id, name, quantity, is_bought, user_id):
    query_sql = "update shopping_list_items SET name=%s, quantity=%s, is_bought=%s where id=%s and user_id=%s"
    execute_sql_query(query_sql, [name, quantity, is_bought, item_id, user_id])
