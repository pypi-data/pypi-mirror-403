"""The 50five API code"""

import logging
from enum import StrEnum
from json import dumps
from typing import Any

from aiohttp import ClientSession

from .decorators import authenticated
from .requests import Request


class Market(StrEnum):
    BELUX = "belux"
    NL = "nl"
    DE = "de"
    FR = "fr"
    UK = "uk"


class Api:
    """Class to make API requests"""

    def __init__(
        self, session: ClientSession, email: str, password: str, market: Market
    ):
        """Initilaize the session."""
        self.session = session
        self.email = email
        self.password = password
        self.url = f"https://50five-s{market}.evc-net.com"
        self.api = f"{self.url}/api/ajax"
        self.logger = logging.getLogger("50five")

    async def logout(self) -> None:
        async with self.session.get(f"{self.url}/Logout") as response:
            response.raise_for_status()

    async def login(self) -> bool:
        data = {
            "emailField": self.email,
            "passwordField": self.password,
            "Login": "Log in",
        }
        async with self.session.post(
            url=f"{self.url}/Login/Login", data=data, allow_redirects=False
        ) as response:
            return response.status == 302

    @authenticated
    async def make_requests(self, requests: list[Request]) -> Any:
        params = {"requests": dumps(dict(enumerate([r.request for r in requests])))}
        async with self.session.get(self.api, params=params) as response:
            return await response.json(content_type="text/html")
