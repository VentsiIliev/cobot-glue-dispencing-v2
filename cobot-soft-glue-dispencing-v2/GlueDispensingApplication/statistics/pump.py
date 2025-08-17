from .base import StatisticsBase
from .keys import StatisticKey

class PumpStats:

    @staticmethod
    def _make_key(base_key, pump_id):
        return f"{base_key}_{pump_id}"

    # Pump ON Seconds
    @classmethod
    def get_on_seconds(cls, pump_id):
        return StatisticsBase.get(cls._make_key(StatisticKey.PUMP_ON_SECONDS.value, pump_id)) or 0

    @classmethod
    def set_on_seconds(cls, pump_id, seconds):
        StatisticsBase.set(cls._make_key(StatisticKey.PUMP_ON_SECONDS.value, pump_id), seconds)

    @classmethod
    def increment_on_seconds(cls, pump_id, seconds):
        current = cls.get_on_seconds(pump_id)
        cls.set_on_seconds(pump_id, current + seconds)

    # Pump RPM
    @classmethod
    def get_rpm(cls, pump_id):
        return StatisticsBase.get(cls._make_key(StatisticKey.PUMP_RPM.value, pump_id)) or 0

    @classmethod
    def set_rpm(cls, pump_id, rpm):
        StatisticsBase.set(cls._make_key(StatisticKey.PUMP_RPM.value, pump_id), rpm)

    @classmethod
    def increment_rpm(cls, pump_id, rpm):
        current = cls.get_rpm(pump_id)
        cls.set_rpm(pump_id, current + rpm)
