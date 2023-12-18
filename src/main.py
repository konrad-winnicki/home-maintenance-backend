import os

from api import socketio
from api import app
from db_schema import create_tables


create_tables()

app_profile = os.getenv('APP_PROFILE')
on_local_environment = app_profile == 'dev'
if on_local_environment:
    print('Starting development server on local environment')
    """
    app.run(
        host="0.0.0.0",
        debug=True,
        #ssl_context=('../cert/cert.pem', '../cert/key.pem')
    )
    """
    socketio.run(app, allow_unsafe_werkzeug=True)
