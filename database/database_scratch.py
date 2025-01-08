from collections import defaultdict
from asyncio.queues import Queue

DATA = {
    "money_value": None,
    "language_code": None,
    "money_currency": None,
}

# В базе данных будет использоваться интернационализация
# Зарефакторить под датакласс (Или найти альтернативу именованному кортежу)
CATEGORIES = defaultdict(list)
CATEGORIES["food"].extend(["Полноценная пища", "Фаст-фуд"])


Queues = {}
