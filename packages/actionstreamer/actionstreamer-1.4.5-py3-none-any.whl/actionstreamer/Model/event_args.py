from abc import ABC, abstractmethod

class EventArgs(ABC):
    @abstractmethod
    def to_json(self) -> str:
        pass