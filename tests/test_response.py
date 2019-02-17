import asyncio
import socket

import pytest

import aiohttp
from aiohttp import web
from aiohttp.resolver import DefaultResolver
from aiohttp.test_utils import unused_port

from asmog import AmpioSmog


SENSOR_ID = 16


class FakeResolver:
    _LOCAL_HOST = {0: '127.0.0.1',
                   socket.AF_INET: '127.0.0.1',
                   socket.AF_INET6: '::1'}

    def __init__(self, fakes, *, loop):
        """fakes -- dns -> port dict"""
        self._fakes = fakes
        self._resolver = DefaultResolver(loop=loop)

    async def resolve(self, host, port=0, family=socket.AF_INET):
        fake_port = self._fakes.get(host)
        if fake_port is not None:
            return [{'hostname': host,
                     'host': self._LOCAL_HOST[family], 'port': fake_port,
                     'family': family, 'proto': 0,
                     'flags': socket.AI_NUMERICHOST}]
        else:
            return await self._resolver.resolve(host, port, family)


class FakeAmpio:

    def __init__(self, *, loop):
        self.loop = loop
        self.app = web.Application()
        self.app.router.add_routes(
            [web.get('/api/devices/{sensor_id}', self.last_hour)])
        self.runner = None

    async def start(self):
        port = unused_port()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '127.0.0.1', port)
        await site.start()
        return {'smog1.ampio.pl': port}

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()

    async def last_hour(self, request):
        sensor_id = request.match_info.get('sensor_id')
        if sensor_id == '16':
            return web.json_response(
                {
                    'devName': 'Test sensor',
                    'deviceID': 16,
                    'pm25_0': 27,
                    'pm10_0': 29,
                    'lastPM25': 28,
                    'lastPM10': 30,
                    'lastSeen':
                    '2019-02-17 17:00:18',
                    'lat': 50.35718,
                    'lon': 19.06775,
                    'rssi': -79,
                    'humidity': 47.249001,
                    'pressure': 1021.710022
                }
            )

        elif sensor_id == '10':
            return web.json_response([])

        elif sensor_id == '9':
            return web.Response(text="Hello, world")


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


async def test_response(loop):

    fake_ampio = FakeAmpio(loop=loop)
    info = await fake_ampio.start()
    resolver = FakeResolver(info, loop=loop)
    connector = aiohttp.TCPConnector(loop=loop, resolver=resolver,
                                     ssl=False)

    async with aiohttp.ClientSession(connector=connector,
                                     loop=loop) as session:
        station = AmpioSmog(SENSOR_ID, loop, session)

        # Print details about the given station
        await station.get_data()

        assert station.name == 'Test sensor'
        assert station.pm10 == 30
        assert station.pm2_5 == 28
        assert station.pressure == 1021.710022
        assert station.humidity == 47.249001
        assert station.latitude == 50.35718
        assert station.longitude == 19.06775
        assert station.last_seen == '2019-02-17 17:00:18'

    await fake_ampio.stop()


async def test_empty_response(loop):

    fake_ampio = FakeAmpio(loop=loop)
    info = await fake_ampio.start()
    resolver = FakeResolver(info, loop=loop)
    connector = aiohttp.TCPConnector(loop=loop, resolver=resolver,
                                     ssl=False)

    async with aiohttp.ClientSession(connector=connector,
                                     loop=loop) as session:
        station = AmpioSmog(10, loop, session)

        await station.get_data()

        assert station.pm10 is None
        assert station.pm2_5 is None
        assert station.pressure is None

    await fake_ampio.stop()


async def test_conection_error(loop):

    fake_ampio = FakeAmpio(loop=loop)
    info = {'smog1.ampio.pl': 666}
    resolver = FakeResolver(info, loop=loop)
    connector = aiohttp.TCPConnector(loop=loop, resolver=resolver,
                                     ssl=False)

    async with aiohttp.ClientSession(connector=connector,
                                     loop=loop) as session:
        station = AmpioSmog(10, loop, session)

        await station.get_data()

        assert station.pm10 is None
        assert station.pm2_5 is None
        assert station.pressure is None

    await fake_ampio.stop()


async def test_wrong_response(loop):

    fake_ampio = FakeAmpio(loop=loop)
    info = await fake_ampio.start()
    resolver = FakeResolver(info, loop=loop)
    connector = aiohttp.TCPConnector(loop=loop, resolver=resolver,
                                     ssl=False)

    async with aiohttp.ClientSession(connector=connector,
                                     loop=loop) as session:
        station = AmpioSmog(9, loop, session)

        await station.get_data()

        assert station.pm10 is None
        assert station.pm2_5 is None
        assert station.pressure is None

    await fake_ampio.stop()
