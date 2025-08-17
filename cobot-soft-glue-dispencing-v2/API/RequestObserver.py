from abc import ABC, abstractmethod

class RequestObserver(ABC):
    @abstractmethod
    def onRequestSuccess(self, request, response): pass

    @abstractmethod
    def onRequestFailure(self, request, error): pass
