from datetime import datetime
from database.enums import TimeIntervalsEnum


class DateConfig:
    def __init__(self, date_config: str = None):
        self.date_config = date_config if date_config else self._compute_config()
        for interval, value in zip(TimeIntervalsEnum, self.date_config.split(".")):
            setattr(self, interval.value, value)

    def compare_date_configs(self, obj: "DateConfig") -> list[TimeIntervalsEnum]:
        intervals = []
        for interval in TimeIntervalsEnum:
            if getattr(self, interval.value) == getattr(obj, interval.value):
                continue
            intervals.append(interval.value)
        return intervals

    @staticmethod
    def _compute_config():
        now = datetime.now()
        """deprecated type"""
        old_year_type = now.timestamp() // (60 * 60 * 24)
        year = now.year
        date_config = f"{now.strftime("%j.%W.%m")}.{(now.month - 1) // 3 + 1}.{(now.month - 1) // 6 + 1}.{year}"

        return date_config
