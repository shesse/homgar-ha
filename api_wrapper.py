import time  # noqa: D100

from .const import LOGGER
from .homgarapi.api import HomgarApi, HomgarApiException


class HomgarApiWrapper:
    """Wrapper for Homgar API plus credentials."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize HomgarApiWrapper."""

        self.api: HomgarApi | None = None
        self.username = username
        self.password = password
        self.homes = {}
        self.last_poll = 0
        self.available = True
        LOGGER.debug("Creating new HomgarApi")
        self.api = HomgarApi()

    def authenticate(self):
        """Connect to API."""

        try:
            self.api.ensure_logged_in(self.username, self.password)
        except HomgarApiException as ex:
            LOGGER.error("Error authenticating to Homgar API: %s", ex)
            self.available = False
            LOGGER.debug("Creating new HomgarApi because of error")
            self.api = HomgarApi()
            raise ex from None
        else:
            self.available = True

    def poll(self):
        """Request data from account."""

        now = time.time()
        if now - self.last_poll < 120:
            return

        LOGGER.debug("Polling Homgar API")
        self.last_poll = now

        try:
            self.authenticate()
            api = self.api
            for home in api.get_homes():
                LOGGER.debug("Home: %s %s", home.hid, home.name)
                hubs = {}
                self.homes[home.hid] = hubs
                for hub in api.get_devices_for_hid(home.hid):
                    LOGGER.debug("  - %s", hub)
                    subdevs = {}
                    hubs[hub.mid] = subdevs
                    api.get_device_status(hub)
                    for subdevice in hub.subdevices:
                        LOGGER.debug("    %s", subdevice.name)
                        subdevs[subdevice.address] = subdevice
        except HomgarApiException as ex:
            LOGGER.error("Error polling Homgar API: %s", ex)
            self.available = False
            LOGGER.debug("Creating new HomgarApi because of error")
            self.api = HomgarApi()
            raise ex from None
        else:
            self.available = True
