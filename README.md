## How to build it locally

### Using pip and env separately
1) Create virtual env if not present:
```shell
python -m venv .venv
```
2) Activate the virtual env:
```shell
. .venv/activate
```
3) Install requirements:
```shell
pip install -r requirements.txt
```

### Using pipenv (not used for now)
Activate virtual env:
```shell
pipenv shell
```
Pipenv tool uses `Pipfile` file to create virtual env using defined Python version and library dependencies.
```shell
pipenv install
```
To generate `requirements.txt`:
```shell
pipenv requirements > requirements.txt
```

## Running application locally

To run locally the app in a similar way as it will be run on production it is started using a WSGI http server.
To run it using WSGI http server locally (the app should not start any http server on its own):

```shell
VERCEL=anyvalue uwsgi --http :9090 --wsgi-file main.py --callable app
```

When environment variable is set - the internal http server is not started manually.
