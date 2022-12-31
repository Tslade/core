"""Cover platform for Advantage Air integration."""
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Airtouch 4 covers."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    info = coordinator.data
    entities: list[CoverEntity] = [
        AirtouchGroupVent(coordinator, group["group_number"], info)
        for group in info["groups"]
    ]

    async_add_entities(entities)


class AirtouchGroupVent(CoordinatorEntity, CoverEntity):
    """Airtouch Cover Class."""

    _attr_device_class = CoverDeviceClass.DAMPER
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, coordinator, group_number, info):
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._group_number = group_number
        self._airtouch = coordinator.airtouch
        self._info = info
        self._unit = self._airtouch.GetGroupByGroupNumber(self._group_number)

    @callback
    def _handle_coordinator_update(self):
        self._unit = self._airtouch.GetGroupByGroupNumber(self._group_number)
        return super()._handle_coordinator_update()

    @property
    def is_closed(self) -> bool:
        """Return if vent is fully closed."""
        return self._unit.OpenPercentage == 0

    @property
    def current_cover_position(self) -> int:
        """Return vents current position as a percentage."""
        return self._unit.OpenPercentage

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Airtouch",
            "model": "Airtouch 4",
        }

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return str(self._group_number) + "DAMPER"

    @property
    def name(self) -> str:
        """Return the name of the climate device."""
        return self._unit.GroupName + " Vent"

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Fully open zone vent."""
        self._unit = await self._airtouch.SetGroupToPercentage(self._group_number, 100)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Fully close zone vent."""
        self._unit = await self._airtouch.SetGroupToPercentage(self._group_number, 0)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set zone vent to position."""
        position = round(kwargs[ATTR_POSITION] / 5) * 5
        self._unit = await self._airtouch.SetGroupToPercentage(
            self._group_number, position
        )

