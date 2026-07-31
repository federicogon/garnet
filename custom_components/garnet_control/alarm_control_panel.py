"""alarm_control_panel platform for Garnet Control."""

from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    PARTITION_STATE_ARMED,
    PARTITION_STATE_DISARMED,
    PARTITION_STATE_PRESENT,
    PARTITION_STATE_TRIGGERED,
    PARTITION_STATE_UNCONFIGURED,
)
from .coordinator import GarnetCoordinator

_LOGGER = logging.getLogger(__name__)

# Mapping of the API `estado` values to Home Assistant states
# (see docs/api-notes.md):
#   - "disarm"    -> disarmed
#   - "arm"       -> armed away
#   - "present"   -> armed home (armed with some zones bypassed)
#   - "triggered" -> triggered (the alarm is ringing)
#   - "0"         -> unconfigured partition (no entity is created)
STATE_MAP: dict[str, AlarmControlPanelState] = {
    PARTITION_STATE_DISARMED: AlarmControlPanelState.DISARMED,
    PARTITION_STATE_ARMED: AlarmControlPanelState.ARMED_AWAY,
    PARTITION_STATE_PRESENT: AlarmControlPanelState.ARMED_HOME,
    PARTITION_STATE_TRIGGERED: AlarmControlPanelState.TRIGGERED,
}


def _map_state(estado: str | None) -> AlarmControlPanelState | None:
    """Translate the API `estado` to the Home Assistant state."""
    if estado is None:
        return None
    return STATE_MAP.get(estado)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one entity per configured partition of each system."""
    coordinator: GarnetCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[GarnetAlarmPanel] = []
    for system_id, system in coordinator.data.items():
        for partition, pdata in (system.get("estados") or {}).items():
            # Partitions with state "0" are not configured -> skip them.
            if pdata.get("estado") == PARTITION_STATE_UNCONFIGURED:
                continue
            entities.append(GarnetAlarmPanel(coordinator, system_id, partition))

    async_add_entities(entities)


class GarnetAlarmPanel(CoordinatorEntity[GarnetCoordinator], AlarmControlPanelEntity):
    """Represent a partition of a Garnet Control alarm."""

    _attr_has_entity_name = True
    _attr_code_arm_required = False
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_HOME
    )

    def __init__(
        self,
        coordinator: GarnetCoordinator,
        system_id: str,
        partition: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._system_id = system_id
        self._partition = partition
        self._attr_unique_id = f"{system_id}_{partition}"

    @property
    def _system(self) -> dict:
        """System object from the coordinator."""
        return self.coordinator.data.get(self._system_id) or {}

    @property
    def _partition_data(self) -> dict:
        """Partition data (name, state)."""
        return (self._system.get("estados") or {}).get(self._partition) or {}

    @property
    def name(self) -> str | None:
        """Partition name (used as the entity name)."""
        return self._partition_data.get("nombre")

    @property
    def device_info(self) -> DeviceInfo:
        """Group the partitions under one device per system."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._system_id)},
            name=self._system.get("nombre"),
            manufacturer="Garnet Control",
        )

    @property
    def available(self) -> bool:
        """The entity is available if the system is still in the data."""
        return super().available and self._system_id in self.coordinator.data

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Current state of the partition."""
        return _map_state(self._partition_data.get("estado"))

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Disarm the alarm."""
        await self.coordinator.client.async_disarm(self._system_id, self._partition)
        await self.coordinator.async_request_refresh()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Arm the alarm in 'Away' mode."""
        await self.coordinator.client.async_arm_away(self._system_id, self._partition)
        await self.coordinator.async_request_refresh()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Arm the alarm in 'Home' mode."""
        await self.coordinator.client.async_arm_home(self._system_id, self._partition)
        await self.coordinator.async_request_refresh()
