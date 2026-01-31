from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import Event


class EventResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', event: Optional[Event] = None):
        super().__init__(code, description)
        self.event = event or Event()


class EventListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', event_list: Optional[List[Event]] = None):
        super().__init__(code, description)
        self.event_list = event_list or []