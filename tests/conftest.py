"""Pytest configuration for the Garnet Control tests.

Loads the `garnet_control.api` / `garnet_control.const` modules WITHOUT
executing garnet_control/__init__.py (which imports homeassistant), so the
API-client tests run with just aiohttp — no Home Assistant install required.
"""

from __future__ import annotations

import json
import pathlib
import sys
import types

import pytest

GARNET_DIR = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components"
    / "garnet_control"
)

# Register a lightweight `garnet_control` package pointing at the source
# directory so `from garnet_control.api import ...` resolves its relative
# `from .const import ...` import without triggering the real package __init__.
if "garnet_control" not in sys.modules:
    _pkg = types.ModuleType("garnet_control")
    _pkg.__path__ = [str(GARNET_DIR)]
    sys.modules["garnet_control"] = _pkg


class FakeResponse:
    """Minimal stand-in for aiohttp.ClientResponse usable as async context manager."""

    def __init__(self, status: int, payload: dict) -> None:
        self.status = status
        self._payload = payload

    async def json(self, content_type: str | None = None) -> dict:
        return self._payload

    async def text(self) -> str:
        return json.dumps(self._payload)

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False


class FakeSession:
    """Fake aiohttp.ClientSession that returns queued responses per (method, url).

    `session.request(...)` is a sync call returning an async context manager,
    matching how aiohttp behaves and how GarnetApiClient uses it. Requests are
    recorded in `calls` so tests can assert headers and bodies.
    """

    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], list[FakeResponse]] = {}
        self.calls: list[dict] = []

    def add(self, method: str, url: str, *, status: int = 200, payload: dict) -> None:
        """Queue a response for a (method, url). Repeated calls consume the queue."""
        self._routes.setdefault((method.upper(), url), []).append(
            FakeResponse(status, payload)
        )

    def request(self, method, url, *, json=None, headers=None, timeout=None):  # noqa: A002
        self.calls.append(
            {"method": method, "url": url, "json": json, "headers": headers}
        )
        queue = self._routes.get((method.upper(), url))
        if not queue:
            raise AssertionError(f"Unexpected request: {method} {url}")
        # Keep the last response if the queue would otherwise empty.
        return queue.pop(0) if len(queue) > 1 else queue[0]


@pytest.fixture
def fake_session() -> FakeSession:
    """A FakeSession to inject into GarnetApiClient."""
    return FakeSession()
