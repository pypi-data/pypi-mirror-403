from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import DeviceHealth


class DeviceHealthResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', device_health: Optional[DeviceHealth] = None):
        super().__init__(code, description)
        self.device_health = device_health or DeviceHealth()


class DeviceHealthListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', device_health_list: Optional[List[DeviceHealth]] = None):
        super().__init__(code, description)
        self.device_health_list = device_health_list or []
