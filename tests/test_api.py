"""Tests for GarnetApiClient (runs without Home Assistant)."""

from __future__ import annotations

import pytest

from garnet_control.api import GarnetApiClient, GarnetAuthError
from garnet_control.const import (
    API_BASE,
    AUTH_HEADER,
    CLIENT_HEADER,
    CLIENT_HEADER_VALUE,
)

EMAIL = "user@example.com"
PASSWORD = "secret"


def _login_payload(token: str = "tok123") -> dict:
    return {"success": True, "accessToken": token}


async def test_login_stores_token(fake_session) -> None:
    """A successful login stores the accessToken."""
    fake_session.add("POST", f"{API_BASE}/auth/login", payload=_login_payload("tok123"))
    client = GarnetApiClient(EMAIL, PASSWORD, fake_session)

    await client.async_login()

    assert client._token == "tok123"


async def test_login_without_token_raises(fake_session) -> None:
    """A login response without accessToken raises GarnetAuthError."""
    fake_session.add("POST", f"{API_BASE}/auth/login", payload={"success": True})
    client = GarnetApiClient(EMAIL, PASSWORD, fake_session)

    with pytest.raises(GarnetAuthError):
        await client.async_login()


async def test_get_systems_returns_sistemas(fake_session) -> None:
    """async_get_systems unwraps message.sistemas from the response."""
    fake_session.add("POST", f"{API_BASE}/auth/login", payload=_login_payload())
    fake_session.add(
        "GET",
        f"{API_BASE}/systems/",
        payload={
            "success": True,
            "message": {
                "sistemas": [
                    {
                        "id": "abc",
                        "nombre": "Casa",
                        "estados": {
                            "1": {"nombre": "P1", "estado": "disarm"},
                            "2": {"nombre": "P2", "estado": "present"},
                            "3": {"nombre": "P3", "estado": "0"},
                        },
                    }
                ]
            },
        },
    )
    client = GarnetApiClient(EMAIL, PASSWORD, fake_session)
    await client.async_login()

    systems = await client.async_get_systems()

    assert len(systems) == 1
    assert systems[0]["id"] == "abc"
    assert systems[0]["estados"]["1"]["estado"] == "disarm"
    assert systems[0]["estados"]["2"]["estado"] == "present"


async def test_authenticated_request_sends_required_headers(fake_session) -> None:
    """Every authenticated request carries X-Client-Web and x-access-token."""
    fake_session.add("POST", f"{API_BASE}/auth/login", payload=_login_payload("tok"))
    fake_session.add(
        "GET",
        f"{API_BASE}/systems/",
        payload={"success": True, "message": {"sistemas": []}},
    )
    client = GarnetApiClient(EMAIL, PASSWORD, fake_session)
    await client.async_login()
    await client.async_get_systems()

    systems_call = fake_session.calls[-1]
    assert systems_call["headers"][CLIENT_HEADER] == CLIENT_HEADER_VALUE
    assert systems_call["headers"][AUTH_HEADER] == "tok"


async def test_arm_away_fetches_timeout_and_builds_body(fake_session) -> None:
    """async_arm_away fetches the timeout and posts seq/partNumber/timeout."""
    fake_session.add("POST", f"{API_BASE}/auth/login", payload=_login_payload())
    fake_session.add(
        "GET",
        f"{API_BASE}/systems/sys1/timeout",
        payload={"success": True, "message": {"timeout": 8500}},
    )
    fake_session.add(
        "POST",
        f"{API_BASE}/systems/sys1/commands/arm/away",
        payload={"success": True, "message": {"response": "OK"}},
    )
    client = GarnetApiClient(EMAIL, PASSWORD, fake_session)
    await client.async_login()

    result = await client.async_arm_away("sys1", "1")

    assert result == {"response": "OK"}
    command_call = fake_session.calls[-1]
    assert command_call["json"] == {"seq": "001", "partNumber": "1", "timeout": 8500}


def test_next_seq_increments_and_wraps() -> None:
    """seq starts at 001, increments, and wraps back to 001 after 999."""
    client = GarnetApiClient(EMAIL, PASSWORD, session=None)
    assert client._next_seq() == "001"
    assert client._next_seq() == "002"
    client._seq = 999
    assert client._next_seq() == "001"
