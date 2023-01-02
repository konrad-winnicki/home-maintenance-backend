## How to build it locally

### Using pip and venv
1. Create virtual env if not present:
```shell
python -m venv .venv
```
2. Activate the virtual env:
```shell
. .venv/activate
```
3. Install requirements:
```shell
pip install -r requirements.txt
```

## Running application locally

To run locally the app in a similar way as it will be run on production it is started using a WSGI http server (gunicorn).
To run it the same way locally (the app should not start any http server on its own):

```shell
FLY_APP_NAME=anyvalue gunicorn main:app
```

When environment variable is set - the internal http server is not started.

## Deploying to production

To deploy new version:
```shell
flyctl deploy
```

Checking logs:
```shell
flyctl logs
```

Logging in into production server:
```shell
flyctl ssh issue --agent
flyctl ssh console
```
