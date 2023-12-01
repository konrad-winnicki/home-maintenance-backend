import os

from api import app
from db_schema import create_tables
from oauth import register_oauth_callback

create_tables()
register_oauth_callback(app)

on_local_environment = os.getenv('FLY_APP_NAME') is None
if on_local_environment:
    print('Starting development server')
    app.run(
        debug=True,
        # ssl_context=('cert/cert.pem', 'cert/priv_key.pem')
    )