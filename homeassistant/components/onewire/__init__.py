"""The 1-Wire component."""

import logging

from pyownet import protocol

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .onewirehub import OneWireConfigEntry, OneWireHub

_LOGGER = logging.getLogger(__name__)

_PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: OneWireConfigEntry) -> bool:
    """Set up a 1-Wire proxy for a config entry."""
    onewire_hub = OneWireHub(hass, entry)
    try:
        await onewire_hub.initialize()
    except (
        protocol.ConnError,  # Failed to connect to the server
        protocol.OwnetError,  # Connected to server, but failed to list the devices
    ) as exc:
        raise ConfigEntryNotReady from exc

    entry.runtime_data = onewire_hub

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: OneWireConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    onewire_hub = config_entry.runtime_data
    return not device_entry.identifiers.intersection(
        (DOMAIN, device.id) for device in onewire_hub.devices or []
    )


async def async_unload_entry(
    hass: HomeAssistant, config_entry: OneWireConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, _PLATFORMS)


async def options_update_listener(
    hass: HomeAssistant, entry: OneWireConfigEntry
) -> None:
    """Handle options update."""
    _LOGGER.debug("Configuration options updated, reloading OneWire integration")
    await hass.config_entries.async_reload(entry.entry_id)
