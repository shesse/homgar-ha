"""The homgar integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .api_wrapper import HomgarApiWrapper

## For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]


type HomgarConfigEntry = ConfigEntry[HomgarApiWrapper]


async def async_setup_entry(hass: HomeAssistant, entry: HomgarConfigEntry) -> bool:
    """Set up homgar from a config entry."""

    api = HomgarApiWrapper(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    entry.runtime_data = api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: HomgarConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
