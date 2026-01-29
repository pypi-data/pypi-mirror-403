from abc import ABC, abstractmethod
from typing import Optional

from .models import Mode, TimeGrouping


class Channel:
    def __init__(self, recharge_spot_id: str, channel_id: str):
        self.recharge_spot_id = recharge_spot_id
        self.id = channel_id


class Request(ABC):
    @property
    @abstractmethod
    def service(self) -> str:
        pass

    @property
    @abstractmethod
    def method(self) -> str:
        pass

    @property
    @abstractmethod
    def params(self) -> dict:
        pass

    @property
    def request(self) -> dict:
        return {
            "handler": f"\\LMS\\EV\\AsyncServices\\{self.service}",
            "method": self.method,
            "params": self.params,
        }


class DashboardRequest(Request):
    service = "DashboardAsyncService"


class RechargeSpotsRequest(Request):
    service = "RechargeSpotsAsyncService"


class NetworkOverview(DashboardRequest):
    method = "networkOverview"
    params = {"mode": "id"}


class NetworkOverviewDetails(DashboardRequest):
    method = "networkOverviewDetails"

    def __init__(self, channels: list[Channel]):
        self.channels = channels

    @property
    def params(self) -> dict:
        return {
            "rechargeSpotsChannels": [
                {"i": c.recharge_spot_id, "c": c.id} for c in self.channels
            ],
            "mode": "id",
        }


class SpotsStatus(DashboardRequest):
    method = "spotsStatus"

    def __init__(self, recharge_spot_ids: list[str]):
        self.recharge_spot_ids = recharge_spot_ids

    @property
    def params(self) -> dict[str, list[str]]:
        return {"rechargeSpotIds": self.recharge_spot_ids}


class Usage(DashboardRequest):
    method = "usage"

    def __init__(self, mode: TimeGrouping, maxCache: int = 3600):
        self.mode = mode
        self.maxCache = maxCache

    @property
    def params(self) -> dict[str, str | int]:
        return {"mode": self.mode, "maxCache": self.maxCache}


class TotalUsage(DashboardRequest):
    method = "totalUsage"

    def __init__(
        self,
        mode: Mode,
        recharge_spot_ids: None | list[str] = None,
        maxCache: int = 3600,
    ):
        self.mode = mode
        self.recharge_spot_ids = recharge_spot_ids
        self.maxCache = maxCache

    @property
    def params(self) -> dict:
        to_ret: dict = {"mode": self.mode, "maxCache": self.maxCache}
        if self.recharge_spot_ids:
            to_ret["rechargeSpotIds"] = self.recharge_spot_ids
        return to_ret


class Occupancy(DashboardRequest):
    method = "occupancy"

    def __init__(
        self, recharge_spot_ids: list[str], mode: int = 7, maxCache: int = 3600
    ):
        self.mode = mode
        self.recharge_spot_ids = recharge_spot_ids
        self.maxCache = maxCache

    @property
    def params(self) -> dict:
        return {
            "mode": self.mode,
            "rechargeSpotIds": self.recharge_spot_ids,
            "maxCache": self.maxCache,
        }


class Current(DashboardRequest):
    """Current dashboard request

    :param recharge_spot_ids:
        List of recharge spot ids for which the current graph should be fetched.
    :type recharge_spot_ids: list[str]
    :param mode:
        Messes with the time format and range, 1 and 3 are your safest bet.
    :type mode: int
    """

    method = "current"

    def __init__(self, recharge_spot_ids: Optional[list[str]] = None, mode: int = 1):
        self.mode = mode
        self.recharge_spot_ids = recharge_spot_ids

    @property
    def params(self) -> dict:
        return {
            "mode": self.mode,
            "rechargeSpotIds": self.recharge_spot_ids,
        }


class Overview(RechargeSpotsRequest):
    method = "overview"

    def __init__(self, recharge_spot_id: str):
        self.recharge_spot_id = recharge_spot_id

    @property
    def params(self) -> dict:
        return {"rechargeSpotId": self.recharge_spot_id}


class Log(RechargeSpotsRequest):
    method = "log"

    def __init__(self, channel: Channel):
        self.channel = channel

    @property
    def params(self) -> dict[str, str]:
        return {
            "rechargeSpotId": self.channel.recharge_spot_id,
            "channel": self.channel.id,
        }


class ClientSearch(RechargeSpotsRequest):
    method = "userAccess"

    def __init__(self, recharge_spot_id: str, name: str):
        self.recharge_spot_id = recharge_spot_id
        self.name = name

    @property
    def params(self) -> dict[str, str]:
        return {"rechargeSpotId": self.recharge_spot_id, "input": self.name}


class CardSearch(RechargeSpotsRequest):
    method = "cardAccess"

    def __init__(self, recharge_spot_id: str, customer_id: str):
        self.recharge_spot_id = recharge_spot_id
        self.customer_id = customer_id

    @property
    def params(self) -> dict[str, str]:
        return {"rechargeSpotId": self.recharge_spot_id, "customerId": self.customer_id}


class Action(RechargeSpotsRequest):
    method = "action"


class Start(Action):
    def __init__(self, channel: Channel, customer_id: str, card_id: str) -> None:
        self.channel = channel
        self.customer_id = customer_id
        self.card_id = card_id

    @property
    def params(self) -> dict[str, str | int]:
        return {
            "action": "StartTransaction",
            "rechargeSpotId": self.channel.recharge_spot_id,
            "clickedButtonId": 0,
            "channel": self.channel.id,
            "customer": self.customer_id,
            "card": self.card_id,
        }


class Stop(Action):
    def __init__(self, channel: Channel):
        self.channel = channel

    @property
    def params(self) -> dict[str, str | int]:
        return {
            "action": "StopTransaction",
            "rechargeSpotId": self.channel.recharge_spot_id,
            "clickedButtonId": 0,
            "channel": self.channel.id,
        }
