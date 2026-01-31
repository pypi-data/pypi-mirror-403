from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import EventPreset


class EventPresetResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', event_preset: Optional[EventPreset] = None):
        super().__init__(code, description)
        self.event_preset = event_preset or EventPreset()


class EventPresetListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', event_preset_list: Optional[List[EventPreset]] = None):
        super().__init__(code, description)
        self.event_preset_list = event_preset_list or []