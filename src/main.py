import os

from src.db_schema import create_tables
from src.api import app, socketio

create_tables()

app_profile = os.getenv('APP_PROFILE')
on_local_environment = app_profile == 'local'
if on_local_environment:
    print('Starting development server on local environment')
    socketio.run(app, allow_unsafe_werkzeug=True)
