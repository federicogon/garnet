"""DataUpdateCoordinator for Garnet Control."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GarnetApiClient, GarnetApiError, GarnetAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class GarnetCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Poll the state of the systems via GET /systems/.

    `data` is a dict keyed by system id holding the object as returned by the
    API (includes `nombre` and `estados` per partition).
    """

    def __init__(self, hass: HomeAssistant, client: GarnetApiClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, dict]:
        """Fetch the current state of all systems."""
        try:
            systems = await self.client.async_get_systems()
        except GarnetAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GarnetApiError as err:
            raise UpdateFailed(str(err)) from err

        return {s["id"]: s for s in systems if s.get("id")}
