"""Get the data from an AmpiSmog station."""
import asyncio

import aiohttp

from asmog import AmpioSmog

SENSOR_ID = '16'


async def main():
    """Sample code to retrieve the data from an AmpioSmog station."""
    async with aiohttp.ClientSession() as session:
        station = AmpioSmog(SENSOR_ID, loop, session)

        # Print details about the given station
        await station.get_data()
        print("Name:", station.name)
        print("Last Seen:", station.last_seen)
        print("PM 10:", station.pm10)
        print("PM 25:", station.pm2_5)
        print("Humidity:", station.humidity)
        print("Air Pressure:", station.pressure)
        print("Latitude:", station.latitude)
        print("Longitude:", station.longitude)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
