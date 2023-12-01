from psycopg import Error, OperationalError
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool
from decouple import config
from psycopg.rows import dict_row

from errors import DatabaseError

dbname = config('DB_NAME')
user = config('DB_USER')
port = config('DB_PORT')
password = config('DB_PASSWORD')
host = config('DB_HOST')
conn_info = make_conninfo(dbname=dbname, user=user, port=port, password=password,
                          host=host
                          # host="postgres.c3gdxucwufp2.eu-west-2.rds.amazonaws.com"
                          )

pool = ConnectionPool(conn_info, min_size=5)
print('info', conn_info)
print(pool.get_stats())


def execute_fetch(query_sql, searched_value):
    with pool.connection() as connection:
        cursor = connection.cursor(row_factory=dict_row)
        try:
            cursor.execute(query_sql, searched_value)
            query_result = cursor.fetchone()
        except Error as e:
            print(f"The error '{e}' occurred")
            raise DatabaseError(e)
        return query_result


# TODO: deduplicate execute_fetch_one above
def execute_fetch_all(query_sql, searched_value):
    with pool.connection() as connection:
        cursor = connection.cursor(row_factory=dict_row)
        try:
            cursor.execute(query_sql, searched_value)
            query_result = cursor.fetchall()
        except Error as e:
            print(f"The error '{e}' occurred")
            raise DatabaseError(e)
        return query_result



def check_if_database_is_filled(table_schema):
    query_sql = "select table_name from information_schema.tables where table_schema=%s"
    fetch_result = execute_fetch(query_sql, (table_schema,))
    return fetch_result


def create_table(table_definition):
    with pool.connection() as connection:
        try:
            connection.execute(table_definition)
            print("Table created successfully")
        except OperationalError as e:
            print(f"The error '{e}' occurred")
            raise DatabaseError(e)
