from .base import StatisticsBase
from .keys import StatisticKey

class GeneratorStats:

    @staticmethod
    def get_on_seconds():
        return StatisticsBase.get(StatisticKey.GENERATOR_ON_SECONDS.value) or 0

    @staticmethod
    def set_on_seconds(seconds):
        StatisticsBase.set(StatisticKey.GENERATOR_ON_SECONDS.value, seconds)

    @staticmethod
    def increment_on_seconds(seconds):
        current = GeneratorStats.get_on_seconds()
        GeneratorStats.set_on_seconds(current + seconds)
