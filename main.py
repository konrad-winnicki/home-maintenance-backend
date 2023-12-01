import os

from api import create_tables, app
from oauth import registerOauthCallback

create_tables()
registerOauthCallback(app)

on_local_environment = os.getenv('FLY_APP_NAME') is None
if on_local_environment:
    print('Starting development server')
    app.run(
        debug=True,
        # ssl_context=('cert/cert.pem', 'cert/priv_key.pem')
    )
