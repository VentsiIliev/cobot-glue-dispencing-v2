import json
import os
from enum import Enum
STATISTICS_PATH = os.path.join(os.path.dirname(__file__), "storage", "statistics.json")

class StatisticKey(Enum):
    GENERATOR_ON_SECONDS = "generator_on_seconds"
    PUMP_ON_SECONDS = "pump_on_seconds"
    PUMP_RPM = "pump_rpm"

class Statistics:
    """Class to manage statistics."""
    _stats = None

    @staticmethod
    def get_statistics():
        """Read and return statistics as a dict."""
        if not os.path.exists(STATISTICS_PATH):
            print(f"Statistics file not found at {STATISTICS_PATH}. Returning empty statistics.")
            return {}
        with open(STATISTICS_PATH, "r") as f:
            return json.load(f)

    @staticmethod
    def resetAllToZero():
        """Reset all statistics values to 0, including nested dicts."""
        Statistics._ensure_stats_loaded()

        def zero_values(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    zero_values(value)
                else:
                    d[key] = 0

        zero_values(Statistics._stats)
        Statistics.update_statistics(Statistics._stats)

    @staticmethod
    def update_statistics(new_stats):
        """Update statistics.json with new values."""
        with open(STATISTICS_PATH, "w") as f:
            json.dump(new_stats, f, indent=2)

    @staticmethod
    def _ensure_stats_loaded():
        if Statistics._stats is None:
            Statistics._stats = Statistics.get_statistics()



    @staticmethod
    def clearAll():
        """Clear all statistics."""
        Statistics._stats = {}
        Statistics.update_statistics(Statistics._stats)

    @staticmethod
    def _set_by_key(key, value):
        """Set a statistic value by key."""
        Statistics._ensure_stats_loaded()
        Statistics._stats[key] = value
        Statistics.update_statistics(Statistics._stats)

    @staticmethod
    def _getByKey(key):
        """Get a statistic value by key."""
        Statistics._ensure_stats_loaded()
        return Statistics._stats.get(key, None)

    # GENERATOR ON SECONDS methods
    @staticmethod
    def getGeneratorOnSeconds():
        """Get the total seconds the generator has been on."""
        return Statistics._getByKey(StatisticKey.GENERATOR_ON_SECONDS.value)

    @staticmethod
    def setGeneratorOnSeconds(seconds):
        """Set the total seconds the generator has been on."""
        Statistics._set_by_key(StatisticKey.GENERATOR_ON_SECONDS.value, seconds)
    @staticmethod
    def flatten_stats(stats):
        """Flatten nested dicts in statistics"""
        flat = {}
        for key, value in stats.items():
            if isinstance(value, dict):
                for subkey, subval in value.items():
                    flat[f"{key}_{subkey}"] = subval
            else:
                flat[key] = value
        return flat

    @staticmethod
    def incrementGeneratorOnSeconds(seconds):
        """Increment the total seconds the generator has been on."""
        current_seconds = Statistics.getGeneratorOnSeconds() or 0
        Statistics.setGeneratorOnSeconds(current_seconds + seconds)

    # PUMP ON TIME methods
    @staticmethod
    def getPumpOnTimeById(pump_id):
        """Get the total seconds a specific pump has been on."""
        return Statistics._getByKey(f"{StatisticKey.PUMP_ON_SECONDS.value}_{pump_id}")

    @staticmethod
    def setPumpOnTimeById(pump_id, seconds):
        """Set the total seconds a specific pump has been on."""
        Statistics._set_by_key(f"{StatisticKey.PUMP_ON_SECONDS.value}_{pump_id}", seconds)

    @staticmethod
    def incrementPumpOnTimeById(pump_id, seconds):
        """Increment the total seconds a specific pump has been on."""
        current_seconds = Statistics.getPumpOnTimeById(pump_id) or 0
        Statistics.setPumpOnTimeById(pump_id, current_seconds + seconds)

    # PUMP RPM methods
    @staticmethod
    def getPumpRpmById(pump_id):
        """Get the RPM of a specific pump."""
        return Statistics._getByKey(f"{StatisticKey.PUMP_RPM.value}_{pump_id}")

    @staticmethod
    def setPumpRpmById(pump_id, rpm):
        """Set the RPM of a specific pump."""
        Statistics._set_by_key(f"{StatisticKey.PUMP_RPM.value}_{pump_id}", rpm)

    @staticmethod
    def incrementPumpRpmById(pump_id, rpm):
        """Increment the RPM of a specific pump."""
        current_rpm = Statistics.getPumpRpmById(pump_id) or 0
        Statistics.setPumpRpmById(pump_id, current_rpm + rpm)

# print("Statistics module loaded. Current statistics:", Statistics.get_statistics())

# REST STATISTICS
# Statistics.resetAllToZero()
# print("Statistics module loaded. Current statistics:", Statistics.get_statistics())

# Statistics.setGeneratorOnSeconds(100)
# print("Generator On Seconds:", Statistics.getGeneratorOnSeconds())
# Statistics.incrementGeneratorOnSeconds(50)
# print("Generator On Seconds after increment:", Statistics.getGeneratorOnSeconds())