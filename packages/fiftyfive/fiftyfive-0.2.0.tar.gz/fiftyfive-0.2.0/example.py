#!/usr/bin/env python3
"""Example code."""

import asyncio
import logging
from os import getenv
from sys import stdout

from aiohttp import ClientSession
from dotenv import load_dotenv

from fiftyfive import Api, Market, NetworkOverview, NetworkOverviewDetails, Channel

load_dotenv()


async def main():
    """Main module"""

    async with ClientSession() as session:
        api = Api(session, getenv("50FIVE_EMAIL"), getenv("50FIVE_PASSWORD"), Market.BELUX)

        result = await api.make_requests([NetworkOverview()])
        print(result)

        details = await api.make_requests(
            [
                NetworkOverviewDetails([Channel(charger["IDX"], charger["CHANNEL"])])
                for charger in result[0]
            ]
        )

        [print(d) for d in details[0]]


if __name__ == "__main__":
    logging.basicConfig(stream=stdout, level=logging.DEBUG)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
