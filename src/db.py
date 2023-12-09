import psycopg
from psycopg import Error, OperationalError
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from errors import DatabaseError, ResourceAlreadyExists
from config import config

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
            print("----")
            query_result = cursor.fetchone()
            print("----")
        except Error as e:
            print(f"The error '{e}' occurred")
            raise DatabaseError(e)
        return query_result


def execute_fetch_all(query_sql, searched_value, mapper):
    with pool.connection() as connection:
        cursor = connection.cursor(row_factory=dict_row)
        try:
            cursor.execute(query_sql, searched_value)
            query_result = cursor.fetchall()
            return list(map(mapper, query_result))
        except Error as e:
            print(f"The error '{e}' occurred")
            raise DatabaseError(e)


def execute_sql_query(query_sql, query_values):
    with pool.connection() as connection:
        try:
            connection.execute(query_sql, query_values)
        except psycopg.errors.UniqueViolation:
            raise ResourceAlreadyExists
        except Error as err:
            print(err)


def check_if_database_is_filled(table_schema):
    query_sql = "select table_name from information_schema.tables where table_schema=%s"
    fetch_result = execute_fetch(query_sql, (table_schema,))
    return fetch_result


def create_schema(schema_definition):
    with pool.connection() as connection:
        try:
            connection.execute(schema_definition)
            print("Schema created successfully")
        except OperationalError as e:
            print(f"The error '{e}' occurred")
            raise DatabaseError(e)
