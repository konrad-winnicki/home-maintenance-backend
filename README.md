<!-- omit in toc -->
# Home-maintenance.backend
<br>

<!-- omit in toc -->
## Table of Contents
- [Description](#description)
- [Endpoints](#endpoints)
  - [Root endpoint](#1-root-endpoint)
  - [User authentication](#2-user-authentication)
  - [Homes](#3-homes)
  - [Store](#4-store)
  - [Shopping list](#5-shopping-list)
- [Build and run locally](#how-to-build-it-and-run-locally)
  - [General information](#prepare)
  - [Run database with docker](#run_db_with_docker)
  - [Run backend with docker](#run_backend_with_docker)
- [Test with pytest](#testing-with-pytest)





# Description
It's a REST API application written in Python and deployed on AWS.
The RESTful interface allows users to 
add homes, manage home members, maintain a home store, 
and handle shopping list items. 
Additionally, WebSocket functionality is implemented 
for real-time updates.
<br>

# Endpoints
### 1. Root Endpoint

#### `GET /`

- **Description:** Endpoint for load balancer health check.
- **Response:** 204 No Content

### 2. User Authentication

#### `POST /login`

- **Description:** User authentication using OAuth2 code.
- **Request:** Expects OAuth2 code.
- **Response:** Redirects based on authentication.

### 3. Homes

#### `POST /homes`

- **Description:** Add a new home.
- **Request:**
  - Body: `{ "name": "Home Name" }`
- **Response:** 201 Created with the location header pointing to the newly created home.

#### `GET /homes`

- **Description:** Get a list of homes for the authenticated user.
- **Response:** 200 OK with a list of homes.

#### `POST /homes/{home_id}/members`

- **Description:** Add a member to a specific home.
- **Request:** No request body required.
- **Response:** 204 No Content

#### `DELETE /homes/{home_id}/members/{id}`

- **Description:** Remove a member from a home.
- **Request:** No request body required.
- **Response:** 200 OK with a confirmation message.

### 4. Store

#### `GET /homes/{home_id}/store/products`

- **Description:** Get the list of products in the store inventory for a specific home.
- **Response:** 200 OK with a list of products.

#### `POST /homes/{home_id}/store/products`

- **Description:** Add a new product to the store inventory.
- **Request:**
  - Body: `{ "name": "Product Name", "quantity": 10 }`
- **Response:** 201 Created with the location header pointing to the newly created product.

#### `PUT /homes/{home_id}/store/products/{product_id}`

- **Description:** Update product information.
- **Request:**
  - Body: `{ "name": "New Product Name", "quantity": 20 }`
- **Response:** 200 OK with a confirmation message.

#### `DELETE /homes/{home_id}/store/products/{product_id}`

- **Description:** Remove a product from the store inventory.
- **Request:** No request body required.
- **Response:** 200 OK with a confirmation message.

### 5. Shopping list

#### `POST /homes/{home_id}/cart/items`

- **Description:** Add a new item to the shopping cart.
- **Request:**
  - Body: `{ "name": "Item Name", "quantity": 5 }`
- **Response:** 201 Created with the location header pointing to the newly created item.

#### `GET /homes/{home_id}/cart/items`

- **Description:** Get the list of items in the shopping cart.
- **Response:** 200 OK with a list of items.

#### `POST /homes/{home_id}/cart/items/shoppinglist`

- **Description:** Move missing products to the shopping list.
- **Request:** No request body required.
- **Response:** 201 Created with a confirmation message.

#### `POST /homes/{home_id}/store/products/delivery`

- **Description:** Confirm the purchase of items in the shopping cart.
- **Request:** No request body required.
- **Response:** 200 OK with a confirmation message.

#### `DELETE /homes/{home_id}/cart/items/{id}`

- **Description:** Remove an item from the shopping cart.
- **Request:** No request body required.
- **Response:** 200 OK with a confirmation message.

#### `PUT/PATCH /homes/{home_id}/cart/items/{id}`

- **Description:** Update shopping cart item details.
- **Request:**
  - Body: `{ "name": "New Item Name", "quantity": 10, "is_bought": true }`
- **Response:** 200 OK with a confirmation message.



# How to build it and run locally

- <a id="prepare"></a>
1. Clone the repository:

```shell
git clone https://github.com/konrad-winnicki/home-maintenance-backend.git
```
2. Create virtual env if not present:

```shell
python -m venv .venv
```

3. Activate the virtual env:

```shell
. .venv/activate
```

4. Install requirements:

```shell
pip install -r requirements.txt
```

5. Prepare `.env.local` in the project root directory containing the following variables:
GOOGLE_CLIENT_ID=your google client ID </br>
GOOGLE_CLIENT_SECRET=your google client secret </br>
EXCHANGE_TOKEN_URI=https://oauth2.googleapis.com/token </br>
FRONTEND_REDIRECT_URI=  example: http://localhost:3000/login </br>
OAUTHLIB_INSECURE_TRANSPORT=yes </br>
SECRET_KEY=your secret for JWT encoding </br>
DB_NAME= example:"database" </br>
DB_USER= example:"user" </br>
DB_PORT= default:5432 </br>
DB_HOST=localhost</br>
DB_PASSWORD=exapmple: "password" </br>

You can set up your postgres database on your own or use service defined in the `docker-compose.yaml`.</br>
</br>
To run <a id="run_db_with_docker"></a>database with docker type in root directory: 
```bash
cd docker
docker-compose up postgresdb
```

The `Dockerfile_backend`contain set of instructions and configurations to build a docker container images for frontend and backend.</br>
</br>
To run <a id="run_backend_with_docker"></a>backend with docker:
1. Prepare `.env.docker` in the project root directory containing most of the same key-value pairs as .env.local.
2. Set up `DB_HOST`=postgresdb
```bash
cd docker
docker-compose up backend
```

# Testing with pytest
1. Prepare `.env.test` in the project root directory containing the following key-value pairs:
DB_NAME=test </br>
DB_USER=user </br>
DB_PORT=5432 </br>
DB_HOST=localhost </br>
DB_PASSWORD=password </br>
SECRET_KEY= secret_value </br>
</br>
2. To run api tests type in root directory:
```shell
pytest tests/test_api.py
```


3. To run service tests type:
```shell
pytest tests/test_service.py
```


