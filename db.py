# module db.py in your program
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool
from decouple import config

# TODO: move to db module
db_password = config('POSTGRES_PASSWORD')
conninfo = make_conninfo(dbname="postgres", user="postgres", port=5432, password=db_password,
                         host="postgres.c3gdxucwufp2.eu-west-2.rds.amazonaws.com")

pool = ConnectionPool(conninfo, min_size=5)
