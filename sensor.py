"""Homgar sensor platform for Home Assistant."""

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import DEFAULT_TIME_ZONE  # noqa: D100

from . import HomgarConfigEntry
from .api_wrapper import HomgarApiWrapper
from .const import DOMAIN, LOGGER


class HomgarWaterflowSensorBase(SensorEntity):
    """Sensor for homgar waterflow meter account."""

    def __init__(
        self, apiWrapper: HomgarApiWrapper, hid: str, mid: str, address: str, attr: str
    ) -> None:
        """Initialize a sensor for a HomGar device."""

        LOGGER.info("HomgarSensorBase %s init", attr)
        self._apiWrapper = apiWrapper
        self._hid = hid
        self._mid = mid
        self._address = address

        self._attr_unique_id = f"{hid}_{mid}_{address} {attr}"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, f"meter {mid}_{address}")},
            manufacturer="RainPoint",
            model="Water Flow Meter",
            name=f"RainPoint Water Flow Meter {mid} ({address})",
            via_device=(DOMAIN, f"hub {mid}"),
        )

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        subdevice = (
            self._apiWrapper.homes.get(self._hid, {})
            .get(self._mid, {})
            .get(self._address)
        )
        if subdevice is None:
            LOGGER.warning(
                "HomgarWaterflowSensor: cannot find subdevice for %s/%s/%s",
                self._hid,
                self._mid,
                self._address,
            )
            return 0.0
        return self.extractNativeValue(subdevice)

    def extractNativeValue(self, subdevice) -> float:
        """Extract the native value from the subdevice."""
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        subdevice = (
            self._apiWrapper.homes.get(self._hid, {})
            .get(self._mid, {})
            .get(self._address)
        )
        return self._apiWrapper.available and subdevice is not None

    def update(self) -> None:
        """Update device state."""
        LOGGER.info("Poll has been called")

        self._apiWrapper.poll()


class HomgarWaterflowSensorTotalUsage(HomgarWaterflowSensorBase):
    """Sensor for homgar waterflow meter account."""

    def __init__(
        self, apiWrapper: HomgarApiWrapper, hid: str, mid: str, address: str
    ) -> None:
        """Initialize a sensor for a HomGar device."""

        super().__init__(apiWrapper, hid, mid, address, "totalUsage")

        self._attr_native_unit_of_measurement = "L"
        self._attr_device_class = SensorDeviceClass.WATER
        self._attr_state_class = SensorStateClass.TOTAL

    def extractNativeValue(self, subdevice) -> float:
        """Extract the native value from the subdevice."""
        return subdevice.totalUsage


class HomgarWaterflowSensorTimestamp(HomgarWaterflowSensorBase):
    """Sensor for homgar waterflow meter account."""

    def __init__(
        self, apiWrapper: HomgarApiWrapper, hid: str, mid: str, address: str
    ) -> None:
        """Initialize a sensor for a HomGar device."""

        super().__init__(apiWrapper, hid, mid, address, "timestamp")

        self._attr_native_unit_of_measurement = None
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_state_class = None

    def extractNativeValue(self, subdevice) -> datetime:
        """Extract the native value from the subdevice."""
        return subdevice.timestamp.replace(tzinfo=DEFAULT_TIME_ZONE)


class HomgarWaterflowSensorRfRssi(HomgarWaterflowSensorBase):
    """Sensor for homgar waterflow meter account."""

    def __init__(
        self, apiWrapper: HomgarApiWrapper, hid: str, mid: str, address: str
    ) -> None:
        """Initialize a sensor for a HomGar device."""

        super().__init__(apiWrapper, hid, mid, address, "rf_rssi")

        self._attr_native_unit_of_measurement = "dBm"
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_state_class = SensorStateClass.MEASUREMENT

    def extractNativeValue(self, subdevice) -> int:
        """Extract the native value from the subdevice."""
        return subdevice.rf_rssi


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HomgarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Homgar sensor devices."""

    LOGGER.info("Homgar async_setup_entry")
    await hass.async_add_executor_job(
        entry.runtime_data.poll,
    )
    LOGGER.info("Initial Homgar poll done")

    LOGGER.info("Hass TZ=%s", DEFAULT_TIME_ZONE)

    device_registry = dr.async_get(hass)

    entities = []
    for hid, hubs in entry.runtime_data.homes.items():
        LOGGER.info("Setup hid=%s", hid)
        for mid, devices in hubs.items():
            LOGGER.info("Setup mid=%s", mid)
            device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, f"hub {mid}")},
                manufacturer="RainPoint",
                model="Mini Box Hub",
                name="RainPoint Mini Box Hub",
            )
            for address, device in devices.items():
                if device.FRIENDLY_DESC == "Water Flow Meter":
                    LOGGER.info("Setup address=%s", address)
                    entities.append(
                        HomgarWaterflowSensorTotalUsage(
                            entry.runtime_data, hid, mid, address
                        )
                    )
                    entities.append(
                        HomgarWaterflowSensorTimestamp(
                            entry.runtime_data, hid, mid, address
                        )
                    )
                    entities.append(
                        HomgarWaterflowSensorRfRssi(
                            entry.runtime_data, hid, mid, address
                        )
                    )
                else:
                    LOGGER.info(
                        "Skipping address=%s, desc=%s",
                        address,
                        device.FRIENDLY_DESC,
                    )
    async_add_entities(entities)
    LOGGER.info("Found a total of %d sensors", len(entities))
