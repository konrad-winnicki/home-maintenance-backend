import os
from decouple import config, Config, RepositoryEnv

from api import app
from db_schema import create_tables

create_tables()

on_local_environment = os.getenv('FLY_APP_NAME') is None
if on_local_environment:
    print('Starting development server')
    config = Config(RepositoryEnv(config("DOTENV_FILE", "../.env_dev")))
    app.run(
        debug=True,
        # ssl_context=('cert/cert.pem', 'cert/priv_key.pem')
    )
