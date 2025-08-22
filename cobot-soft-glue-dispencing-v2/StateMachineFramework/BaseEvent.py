from abc import ABC, abstractmethod

class BaseEvent(ABC):
    """Base class for all events"""
    @property
    @abstractmethod
    def name(self) -> str:
        pass