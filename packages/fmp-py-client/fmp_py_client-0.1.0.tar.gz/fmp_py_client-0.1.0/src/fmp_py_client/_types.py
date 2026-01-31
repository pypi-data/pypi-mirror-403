"""Type aliases and enumerations for the FMP client."""

from enum import StrEnum
from typing import Any

type JSONObject = dict[str, Any]
type JSONArray = list[JSONObject]


class Period(StrEnum):
    """Financial reporting period."""

    ANNUAL = "annual"
    QUARTER = "quarter"


class Timeframe(StrEnum):
    """Technical indicator timeframe."""

    ONE_MIN = "1min"
    FIVE_MIN = "5min"
    FIFTEEN_MIN = "15min"
    THIRTY_MIN = "30min"
    ONE_HOUR = "1hour"
    FOUR_HOUR = "4hour"
    ONE_DAY = "1day"
