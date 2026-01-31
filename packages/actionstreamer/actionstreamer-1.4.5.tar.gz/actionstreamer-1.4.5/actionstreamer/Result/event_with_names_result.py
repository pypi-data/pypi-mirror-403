from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import EventWithNames


class EventWithNamesResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', event_with_names: Optional[EventWithNames] = None):
        super().__init__(code, description)
        self.event_with_names = event_with_names or EventWithNames()


class EventWithNamesListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', event_with_names_list: Optional[List[EventWithNames]] = None):
        super().__init__(code, description)
        self.event_with_names_list = event_with_names_list or []