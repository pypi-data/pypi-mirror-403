from datetime import date, datetime

from moysklad_api.methods import MSMethod
from moysklad_api.types import MetaArray, Profit


class GetProfit(MSMethod):
    __return__ = MetaArray[Profit]
    __api_method__ = "report/profit/by{type}"
    moment_from: str | date | datetime | None = None
    moment_to: str | date | datetime | None = None
