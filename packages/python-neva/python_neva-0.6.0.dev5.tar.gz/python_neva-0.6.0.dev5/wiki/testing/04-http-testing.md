# HTTP Testing

Neva provides an `http_client` fixture for testing your API endpoints. This fixture uses `httpx.AsyncClient` with ASGI transport, allowing you to make HTTP requests to your application without starting a real server.

## Basic Usage

```python
from httpx import AsyncClient
from neva.arch import App


async def test_endpoint(webapp: App, http_client: AsyncClient) -> None:
    # Define a route on the webapp
    @webapp.get("/hello")
    async def hello() -> dict:
        return {"message": "Hello, World!"}

    # Make a request using the http_client
    response = await http_client.get("/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}
```

## How It Works

The `http_client` fixture:
1. Takes the `webapp` fixture as a dependency
2. Creates an `httpx.AsyncClient` with `ASGITransport`
3. Sets the base URL to `http://localhost:8000`
4. Yields the client for your test
5. Properly closes the client after the test

This approach means:
- No real HTTP server is started
- Requests are handled directly by the ASGI application
- Tests run faster and are more isolated

## HTTP Methods

The `AsyncClient` supports all standard HTTP methods:

```python
from httpx import AsyncClient
from neva.arch import App


async def test_http_methods(webapp: App, http_client: AsyncClient) -> None:
    @webapp.get("/items")
    async def list_items() -> list:
        return [{"id": 1}, {"id": 2}]

    @webapp.post("/items")
    async def create_item(data: dict) -> dict:
        return {"id": 3, **data}

    @webapp.put("/items/{item_id}")
    async def update_item(item_id: int, data: dict) -> dict:
        return {"id": item_id, **data}

    @webapp.delete("/items/{item_id}")
    async def delete_item(item_id: int) -> dict:
        return {"deleted": item_id}

    # GET
    response = await http_client.get("/items")
    assert response.status_code == 200

    # POST with JSON body
    response = await http_client.post("/items", json={"name": "New Item"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Item"

    # PUT with JSON body
    response = await http_client.put("/items/1", json={"name": "Updated"})
    assert response.status_code == 200

    # DELETE
    response = await http_client.delete("/items/1")
    assert response.status_code == 200
```

## Testing with Request Data

### JSON Body

```python
async def test_json_body(webapp: App, http_client: AsyncClient) -> None:
    @webapp.post("/users")
    async def create_user(user: dict) -> dict:
        return user

    response = await http_client.post(
        "/users",
        json={"name": "John", "email": "john@example.com"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "John"
```

### Query Parameters

```python
async def test_query_params(webapp: App, http_client: AsyncClient) -> None:
    @webapp.get("/search")
    async def search(q: str, limit: int = 10) -> dict:
        return {"query": q, "limit": limit}

    response = await http_client.get("/search", params={"q": "test", "limit": 5})

    assert response.status_code == 200
    assert response.json() == {"query": "test", "limit": 5}
```

### Headers

```python
async def test_headers(webapp: App, http_client: AsyncClient) -> None:
    @webapp.get("/protected")
    async def protected(authorization: str = Header()) -> dict:
        return {"token": authorization}

    response = await http_client.get(
        "/protected",
        headers={"Authorization": "Bearer my-token"}
    )

    assert response.status_code == 200
```

### Form Data

```python
async def test_form_data(webapp: App, http_client: AsyncClient) -> None:
    @webapp.post("/login")
    async def login(username: str = Form(), password: str = Form()) -> dict:
        return {"username": username}

    response = await http_client.post(
        "/login",
        data={"username": "john", "password": "secret"}
    )

    assert response.status_code == 200
```

## Testing Error Responses

```python
from fastapi import HTTPException


async def test_error_responses(webapp: App, http_client: AsyncClient) -> None:
    @webapp.get("/items/{item_id}")
    async def get_item(item_id: int) -> dict:
        if item_id == 404:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"id": item_id}

    # Success case
    response = await http_client.get("/items/1")
    assert response.status_code == 200

    # Error case
    response = await http_client.get("/items/404")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"
```

## Testing with Dependencies

When your routes use dependency injection:

```python
from dishka.integrations.fastapi import FromDishka
from httpx import AsyncClient
from neva.arch import App

from myapp.services import UserService


async def test_route_with_dependencies(
    webapp: App,
    http_client: AsyncClient
) -> None:
    @webapp.get("/users/{user_id}")
    async def get_user(
        user_id: int,
        user_service: FromDishka[UserService]
    ) -> dict:
        user = await user_service.get(user_id)
        return {"id": user.id, "name": user.name}

    response = await http_client.get("/users/1")
    assert response.status_code == 200
```

## Testing Response Properties

```python
async def test_response_properties(webapp: App, http_client: AsyncClient) -> None:
    @webapp.get("/data")
    async def get_data() -> Response:
        return Response(
            content='{"key": "value"}',
            media_type="application/json",
            headers={"X-Custom-Header": "custom-value"}
        )

    response = await http_client.get("/data")

    # Status code
    assert response.status_code == 200

    # Headers
    assert response.headers["content-type"] == "application/json"
    assert response.headers["x-custom-header"] == "custom-value"

    # Body
    assert response.json() == {"key": "value"}
    assert response.text == '{"key": "value"}'
```

## Organizing HTTP Tests

For larger test suites, consider organizing tests by resource:

```python
from httpx import AsyncClient
from neva.arch import App


class TestUsersAPI:
    """Tests for the /users endpoints."""

    async def test_list_users(self, webapp: App, http_client: AsyncClient) -> None:
        # Register routes and test...
        pass

    async def test_create_user(self, webapp: App, http_client: AsyncClient) -> None:
        pass

    async def test_get_user(self, webapp: App, http_client: AsyncClient) -> None:
        pass


class TestOrdersAPI:
    """Tests for the /orders endpoints."""

    async def test_list_orders(self, webapp: App, http_client: AsyncClient) -> None:
        pass
```
