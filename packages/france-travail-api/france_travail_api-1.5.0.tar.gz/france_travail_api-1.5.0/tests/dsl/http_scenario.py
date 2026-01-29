from __future__ import annotations

import http
import uuid
from dataclasses import dataclass
from typing import Any

from france_travail_api.http_transport._http_client import HttpClient
from france_travail_api.http_transport._http_response import HTTPResponse


@dataclass
class HttpScenario:
    _client: HttpClient | None = None
    _response: HTTPResponse | None = None
    _exception: Exception | None = None

    def integration(self) -> "HttpScenario":
        self._client = HttpClient()
        return self

    def with_client(self, client: HttpClient) -> "HttpScenario":
        self._client = client
        return self

    def when_get(self, url: str, headers: dict[str, str] | None = None) -> "HttpScenario":
        self._ensure_client()
        try:
            self._response = self._client.get(url, headers=headers)
        except Exception as exc:  # pragma: no cover - used by expectations
            self._exception = exc
        return self

    async def when_get_async(self, url: str, headers: dict[str, str] | None = None) -> "HttpScenario":
        self._ensure_client()
        try:
            self._response = await self._client.get_async(url, headers=headers)
        except Exception as exc:  # pragma: no cover - used by expectations
            self._exception = exc
        return self

    def when_post(self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> "HttpScenario":
        self._ensure_client()
        try:
            self._response = self._client.post(url, payload=payload, headers=headers)
        except Exception as exc:  # pragma: no cover - used by expectations
            self._exception = exc
        return self

    async def when_post_async(
        self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None
    ) -> "HttpScenario":
        self._ensure_client()
        try:
            self._response = await self._client.post_async(url, payload=payload, headers=headers)
        except Exception as exc:  # pragma: no cover - used by expectations
            self._exception = exc
        return self

    def then_status_is(self, status: http.HTTPStatus) -> "HttpScenario":
        self._ensure_response()
        assert self._response.status_code == status
        return self

    def then_body_is(self, expected: Any) -> "HttpScenario":
        self._ensure_response()
        assert self._response.body == expected
        return self

    def then_body_contains(self, path: list[str], expected: Any) -> "HttpScenario":
        self._ensure_response()
        current = self._response.body
        for key in path:
            current = current[key]
        assert current == expected
        return self

    def then_request_id_is_uuid(self) -> "HttpScenario":
        self._ensure_response()
        assert uuid.UUID(str(self._response.request_id))
        return self

    def then_exception_is(self, exception_type: type[Exception], match: str | None = None) -> "HttpScenario":
        if self._exception is None:
            raise AssertionError("Expected exception to be captured")
        assert isinstance(self._exception, exception_type)
        if match is not None:
            assert match in str(self._exception)
        return self

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

    def __enter__(self) -> "HttpScenario":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _ensure_client(self) -> None:
        if self._client is None:
            raise ValueError("HTTP client must be configured before request")

    def _ensure_response(self) -> None:
        if self._response is None:
            raise AssertionError("Expected response to be present")


def http_scenario() -> HttpScenario:
    return HttpScenario()
