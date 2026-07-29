"""Garnet Control API client.

Wraps the authentication and API calls used by the web app
https://web.garnetcontrol.app/. See docs/api-notes.md for the detail of each endpoint.
"""

from __future__ import annotations

import asyncio
import logging

import aiohttp

from .const import (
    API_BASE,
    AUTH_HEADER,
    CLIENT_HEADER,
    CLIENT_HEADER_VALUE,
    CMD_ARM_AWAY,
    CMD_ARM_HOME,
    CMD_DISARM,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class GarnetApiError(Exception):
    """Generic API error (network, unexpected response, etc.)."""


class GarnetAuthError(GarnetApiError):
    """Invalid credentials or rejected token."""


class GarnetApiClient:
    """Asynchronous Garnet Control API client."""

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the client.

        `session` is Home Assistant's shared ClientSession.
        """
        self._email = email
        self._password = password
        self._session = session
        self._token: str | None = None
        # `seq` is a per-session command counter managed by the client:
        # it starts at 001 and increments for each command sent to the alarm
        # (arm/disarm). It wraps back to 001 after 999.
        self._seq = 0

    # -- Authentication -------------------------------------------------------

    async def async_login(self) -> None:
        """Authenticate and store the accessToken."""
        data = await self._request(
            "POST",
            "/auth/login",
            json={"email": self._email, "password": self._password},
            authed=False,
        )
        token = data.get("accessToken")
        if not token:
            raise GarnetAuthError("Login did not return an accessToken")
        self._token = token
        _LOGGER.debug("Login successful for %s", self._email)

    # -- Reads ----------------------------------------------------------------

    async def async_get_systems(self) -> list[dict]:
        """Return the list of systems/alarms (`message.sistemas`)."""
        data = await self._request("GET", "/systems/")
        message = data.get("message") or {}
        return message.get("sistemas") or []

    async def async_get_timeout(self, system_id: str) -> int:
        """Get the `timeout` to use in arm/disarm commands."""
        data = await self._request("GET", f"/systems/{system_id}/timeout")
        message = data.get("message") or {}
        timeout = message.get("timeout")
        if timeout is None:
            raise GarnetApiError("The /timeout endpoint did not return 'timeout'")
        return int(timeout)

    # -- Commands -------------------------------------------------------------

    async def async_arm_away(self, system_id: str, partition: str) -> dict:
        """Arm the alarm in 'Away' mode (armed_away)."""
        return await self._send_command(system_id, partition, CMD_ARM_AWAY)

    async def async_arm_home(self, system_id: str, partition: str) -> dict:
        """Arm the alarm in 'Home' mode (armed_home)."""
        return await self._send_command(system_id, partition, CMD_ARM_HOME)

    async def async_disarm(self, system_id: str, partition: str) -> dict:
        """Disarm the alarm."""
        return await self._send_command(system_id, partition, CMD_DISARM)

    async def _send_command(
        self, system_id: str, partition: str, command_path: str
    ) -> dict:
        """Send a command to the alarm with the correct `timeout` and `seq`."""
        timeout = await self.async_get_timeout(system_id)
        body = {
            "seq": self._next_seq(),
            "partNumber": str(partition),
            "timeout": timeout,
        }
        data = await self._request(
            "POST",
            f"/systems/{system_id}/commands/{command_path}",
            json=body,
        )
        return data.get("message") or {}

    def _next_seq(self) -> str:
        """Return the next `seq` (001..999, then wraps back to 001)."""
        self._seq = (self._seq % 999) + 1
        return f"{self._seq:03d}"

    # -- Internal HTTP --------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        authed: bool = True,
        _retry: bool = True,
    ) -> dict:
        """Make an API request and validate the response.

        Retries once after re-authenticating if the token was rejected (401/403).
        """
        if authed and self._token is None:
            await self.async_login()

        # The API requires this header on every request.
        headers = {CLIENT_HEADER: CLIENT_HEADER_VALUE}
        if authed and self._token:
            headers[AUTH_HEADER] = self._token

        url = f"{API_BASE}{path}"
        try:
            async with self._session.request(
                method,
                url,
                json=json,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                if resp.status in (401, 403):
                    if authed and _retry:
                        _LOGGER.debug("Token rejected, retrying login")
                        self._token = None
                        await self.async_login()
                        return await self._request(
                            method, path, json=json, authed=authed, _retry=False
                        )
                    raise GarnetAuthError(f"Unauthorized ({resp.status})")

                if resp.status >= 400:
                    text = await resp.text()
                    raise GarnetApiError(f"HTTP {resp.status}: {text[:200]}")

                payload = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise GarnetApiError(f"Network error: {err}") from err
        except asyncio.TimeoutError as err:
            raise GarnetApiError("Timeout on the API request") from err

        if not isinstance(payload, dict) or not payload.get("success", False):
            raise GarnetApiError(f"Unsuccessful API response: {payload}")

        return payload
