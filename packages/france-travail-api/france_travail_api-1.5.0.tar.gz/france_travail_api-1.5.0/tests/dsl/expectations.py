from __future__ import annotations

from typing import Any

import pytest


class Expectation:
    def __init__(self, value: Any):
        self._value = value

    def to_equal(self, expected: Any) -> None:
        assert self._value == expected

    def to_contain(self, expected: Any) -> None:
        assert expected in self._value

    def to_not_contain(self, expected: Any) -> None:
        assert expected not in self._value

    def to_start_with(self, expected: str) -> None:
        assert str(self._value).startswith(expected)

    def to_be_instance_of(self, expected_type: type) -> None:
        assert isinstance(self._value, expected_type)

    def to_all_be_instance_of(self, expected_type: type) -> None:
        assert all(isinstance(item, expected_type) for item in self._value)

    def to_be_truthy(self) -> None:
        assert bool(self._value)

    def to_be_falsey(self) -> None:
        assert not bool(self._value)

    def to_raise(self, exception_type: type[BaseException], match: str | None = None) -> None:
        if not callable(self._value):
            raise AssertionError("Expected a callable to raise")
        with pytest.raises(exception_type, match=match):
            self._value()

    async def to_raise_async(self, exception_type: type[BaseException], match: str | None = None) -> None:
        if not callable(self._value):
            raise AssertionError("Expected a callable to raise")
        with pytest.raises(exception_type, match=match):
            await self._value()  # type: ignore[func-returns-value]


def expect(value: Any) -> Expectation:
    return Expectation(value)
