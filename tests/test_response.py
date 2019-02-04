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
            [web.get('/lastHour/{sensor_id}', self.last_hour)])
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
                [
                    {
                        "CZAS": "2019-02-04 20:38:52",
                        "PM25": 50,
                        "PM10": 61,
                        "ID": 7529776,
                        "humidity": 75.050003,
                        "temperature": 13.48,
                        "pressure": 1028.680054
                    },
                    {
                        "CZAS": "2019-02-04 20:48:45",
                        "PM25": 48,
                        "PM10": 62,
                        "ID": 7529777,
                        "humidity": 75.820999,
                        "temperature": 12.18,
                        "pressure": 1029.319946
                    },
                    {
                        "CZAS": "2019-02-04 20:58:37",
                        "PM25": 49,
                        "PM10": 59,
                        "ID": 7529778,
                        "humidity": 78.346001,
                        "temperature": 12.49,
                        "pressure": 1029.02002
                    },
                    {
                        "CZAS": "2019-02-04 21:08:28",
                        "PM25": 49,
                        "PM10": 59,
                        "ID": 7529779,
                        "humidity": 82.68,
                        "temperature": 10.48,
                        "pressure": 1029.560059
                    },
                    {
                        "CZAS": "2019-02-04 21:09:21",
                        "PM25": 43,
                        "PM10": 53,
                        "ID": 7529780,
                        "humidity": 74.112,
                        "temperature": 12.8,
                        "pressure": 1028.880005
                    },
                    {
                        "CZAS": "2019-02-04 21:19:12",
                        "PM25": 57,
                        "PM10": 76,
                        "ID": 7529781,
                        "humidity": 74.883003,
                        "temperature": 13.06,
                        "pressure": 1029.380005
                    },
                    {
                        "CZAS": "2019-02-04 21:29:04",
                        "PM25": 62,
                        "PM10": 79,
                        "ID": 7529782,
                        "humidity": 77.080002,
                        "temperature": 12.13,
                        "pressure": 1029.810059
                    }
                ]
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

        assert station.pm10 == 79
        assert station.pm2_5 == 62
        assert station.temperature == 12.13
        assert station.pressure == 1029.810059

        # assert False

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
        assert station.temperature is None
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
        assert station.temperature is None
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
        assert station.temperature is None
        assert station.pressure is None

    await fake_ampio.stop()
