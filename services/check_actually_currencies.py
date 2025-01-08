import asyncio
import json
from decimal import Decimal

import redis
import aiohttp
from aiohttp import ClientResponse

from custom_types.types import DefaultMoneyUnit
from database.enums import MonetaryCurrenciesEnum

r = redis.Redis(host="localhost", port=6379, db=0, protocol=3, decode_responses=True)


async def get_valid_expenses(money_value: str | float | Decimal,
                             default_currency: str = MonetaryCurrenciesEnum.usd.value) -> dict[str, str]:
    redis_connection = redis.Redis(host="localhost", port=6379, db=0, protocol=3, decode_responses=True)
    currencies = await get_actually_currencies(redis_connection=redis_connection)
    money_value = Decimal(str(money_value))
    result = {}

    for cur in MonetaryCurrenciesEnum:
        if cur.value == default_currency:
            result[cur.value] = money_value.__str__()
        elif cur.value == "usd":
            result[cur.value] = DefaultMoneyUnit(
                money_value / Decimal(currencies.get(default_currency.upper()))
            ).__str__()
        else:
            result[cur.value] = DefaultMoneyUnit(
                str(money_value / Decimal(currencies.get(default_currency.upper())) * Decimal(currencies.get(cur.value.upper())))
            ).__str__()
    return result


async def get_actually_currencies(redis_connection: redis.Redis) -> dict[str, str | Decimal]:
    if not redis_connection.get("rates"):
        async with aiohttp.ClientSession() as session:
            response: ClientResponse = await session.get('https://openexchangerates.org/api/latest.json',
                                                         params={"app_id": r"41859edd09c442e186b9a138e677addc"})
        rates = (await response.json()).get("rates")
        is_set = redis_connection.set("rates", json.dumps(rates), ex=3600)
        save = redis_connection.bgsave()
        print("Request to currencies api [GET]")
        return rates
    return json.loads(redis_connection.get("rates"))
