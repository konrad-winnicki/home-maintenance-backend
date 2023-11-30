# module db.py in your program
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool
from decouple import config
from psycopg.rows import dict_row
# TODO: move to db module
dbname = config('DB_NAME')
print(dbname)

user = config('DB_USER')
print(user)
port = config('DB_PORT')
password = config('DB_PASSWORD')
host = config('DB_HOST')
conninfo = make_conninfo(dbname=dbname, user=user, port=port, password=password,
                         host=host
                         #host="postgres.c3gdxucwufp2.eu-west-2.rds.amazonaws.com"
                         )

pool = ConnectionPool(conninfo, min_size=5)
print('info', conninfo)
print(pool.get_stats())



def execute_fetch(query_sql, searched_value):
    with pool.connection() as connection:
        cursor = connection.cursor(row_factory=dict_row)
        try:
            cursor.execute(query_sql, searched_value)
            query_result = cursor.fetchone()
        except Error as e:
            print(f"The error '{e}' occurred")
        return query_result
def check_if_database_is_filled(table_schema):
    query_sql = "select table_name from information_schema.tables where table_schema=%s"
    fetch_result = execute_fetch(query_sql, (table_schema,))
    return fetch_result


print(check_if_database_is_filled('public'))