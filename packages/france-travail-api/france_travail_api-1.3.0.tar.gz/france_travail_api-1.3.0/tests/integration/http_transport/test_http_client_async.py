import http

import httpx
import pytest

from france_travail_api.http_transport._http_client import HttpClient
from tests.dsl import http_scenario


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_client_get_async_returns_response() -> None:
    flow = http_scenario().integration()
    await flow.when_get_async("https://jsonplaceholder.typicode.com/todos/1")
    flow.then_status_is(http.HTTPStatus.OK).then_body_is(
        {"id": 1, "userId": 1, "title": "delectus aut autem", "completed": False}
    )
    flow.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_client_get_async_includes_request_id() -> None:
    flow = http_scenario().integration()
    await flow.when_get_async("https://jsonplaceholder.typicode.com/todos/1")
    flow.then_request_id_is_uuid()
    flow.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_client_get_async_with_custom_headers() -> None:
    flow = http_scenario().integration()
    await flow.when_get_async("https://httpbin.org/headers", headers={"X-Custom-Header": "test-value"})
    flow.then_body_contains(["headers", "Host"], "httpbin.org").then_body_contains(
        ["headers", "X-Custom-Header"], "test-value"
    )
    flow.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_client_close_without_context_manager() -> None:
    flow = http_scenario().with_client(client=HttpClient())
    if flow._client is None:
        raise AssertionError("Expected HTTP client to be present")
    await flow._client.close_async()
    await flow.when_get_async("https://jsonplaceholder.typicode.com/todos/1")
    flow.then_exception_is(RuntimeError)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_client_respects_timeout() -> None:
    flow = http_scenario().with_client(client=HttpClient(timeout=10**-2))

    await flow.when_get_async("https://httpbin.org/delay/1")
    flow.then_exception_is(httpx.TimeoutException)

    flow.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_client_post_returns_response() -> None:
    flow = http_scenario().integration()
    await flow.when_post_async(
        "https://jsonplaceholder.typicode.com/todos",
        payload={"title": "test", "completed": False, "userId": 1},
    )
    flow.then_status_is(http.HTTPStatus.CREATED).then_body_contains(["title"], "test")
    flow.close()
