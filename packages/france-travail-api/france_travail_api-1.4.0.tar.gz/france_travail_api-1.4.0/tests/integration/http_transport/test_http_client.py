import http

import httpx
import pytest

from france_travail_api.http_transport._http_client import HttpClient
from tests.dsl import http_scenario


@pytest.mark.integration
def test_http_client_get_returns_response() -> None:
    with http_scenario().integration() as flow:
        flow.when_get("https://jsonplaceholder.typicode.com/todos/1").then_status_is(http.HTTPStatus.OK).then_body_is(
            {"id": 1, "userId": 1, "title": "delectus aut autem", "completed": False}
        )


@pytest.mark.integration
def test_http_client_get_includes_request_id() -> None:
    with http_scenario().integration() as flow:
        flow.when_get("https://jsonplaceholder.typicode.com/todos/1").then_request_id_is_uuid()


@pytest.mark.integration
def test_http_client_get_with_custom_headers() -> None:
    with http_scenario().integration() as flow:
        flow.when_get("https://httpbin.org/headers", headers={"X-Custom-Header": "test-value"}).then_body_contains(
            ["headers", "Host"], "httpbin.org"
        ).then_body_contains(["headers", "X-Custom-Header"], "test-value")


@pytest.mark.integration
def test_http_client_close_without_context_manager() -> None:
    flow = http_scenario().integration()
    flow.close()
    flow.when_get("https://jsonplaceholder.typicode.com/todos/1").then_exception_is(RuntimeError)


@pytest.mark.integration
def test_http_client_respects_timeout() -> None:
    flow = http_scenario().with_client(client=HttpClient(timeout=10**-3))

    flow.when_get("https://httpbin.org/delay/1").then_exception_is(httpx.TimeoutException)

    flow.close()


@pytest.mark.integration
def test_http_client_post_returns_response() -> None:
    with http_scenario().integration() as flow:
        flow.when_post(
            "https://jsonplaceholder.typicode.com/todos",
            payload={"title": "test", "completed": False, "userId": 1},
        ).then_status_is(http.HTTPStatus.CREATED).then_body_contains(["title"], "test")
