from decimal import Decimal


class DefaultMoneyUnit(Decimal):
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        return instance.quantize(Decimal("0.00"))
