"""An Ampio SMOG API Python client."""
import asyncio
import logging
import socket

import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)
_INSTANCE = 'http://smog1.ampio.pl:3050/api/devices/{id}'


class AmpioSmog:
    """A class for handling connections with the AmpioSmog API."""

    def __init__(self, sensor_id, loop, session):
        """Initialize the connection the AmpioSmog API."""
        self._loop = loop
        self._session = session
        self.data = []
        self.base_url = _INSTANCE.format(id=sensor_id)

    async def get_data(self):
        """Get details of AmpioSmog station."""
        try:
            async with async_timeout.timeout(5, loop=self._loop):
                response = await self._session.get(self.base_url)

            _LOGGER.info(
                "Response from AmpioSmog API: %s", response.status)
            self.data = await response.json()
            _LOGGER.debug(self.data)

        except (asyncio.TimeoutError,
                aiohttp.ClientError,
                socket.gaierror) as err:
            _LOGGER.error("Connection error: %s", err)

        except Exception as err:  # pylint: disable=W0703
            _LOGGER.error("Can not load data from AmpioSmog API: %s", err)

    @property
    def name(self):
        """Return device name."""
        return self.get_value('devName')

    @property
    def pm10(self):
        """Return the particulate matter 10 value."""
        return self.get_value('lastPM10')

    @property
    def pm2_5(self):
        """Return the particulate matter 2.5 value."""
        return self.get_value('lastPM25')

    @property
    def humidity(self):
        """Return the humidity of a station."""
        return self.get_value('humidity')

    @property
    def pressure(self):
        """Return the air pressure at a station."""
        return self.get_value('pressure')

    @property
    def latitude(self):
        """Return sensor latitude."""
        return self.get_value('lat')

    @property
    def longitude(self):
        """Return sensor longitude."""
        return self.get_value('lon')

    @property
    def last_seen(self):
        """Return last seen timestamp."""
        return self.get_value('lastSeen')

    def get_value(self, key):
        """Extract a value for a given key."""
        try:
            if self.data:
                return self.data.get(key, None)
            return None
        except IndexError:
            return None
