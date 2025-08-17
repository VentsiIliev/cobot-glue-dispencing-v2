import json
import os
from .path import STATISTICS_PATH

class StatisticsBase:
    _stats = None

    @classmethod
    def _load(cls):
        if cls._stats is None:
            if not os.path.exists(STATISTICS_PATH):
                cls._stats = {}
            else:
                with open(STATISTICS_PATH, "r") as f:
                    cls._stats = json.load(f)
        return cls._stats

    @classmethod
    def _save(cls):
        with open(STATISTICS_PATH, "w") as f:
            json.dump(cls._stats, f, indent=2)

    @classmethod
    def reset_all(cls):
        def zero_values(d):
            for k, v in d.items():
                if isinstance(v, dict):
                    zero_values(v)
                else:
                    d[k] = 0
        cls._load()
        zero_values(cls._stats)
        cls._save()

    @classmethod
    def clear_all(cls):
        cls._stats = {}
        cls._save()

    @classmethod
    def get(cls, key):
        cls._load()
        return cls._stats.get(key)

    @classmethod
    def set(cls, key, value):
        cls._load()
        cls._stats[key] = value
        cls._save()
