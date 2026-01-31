from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import DeviceHealthRow


class DeviceHealthRowResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', device_health_row: Optional[DeviceHealthRow] = None):
        super().__init__(code, description)
        self.device_health_row = device_health_row or DeviceHealthRow()


class DeviceHealthRowListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', device_health_row_list: Optional[List[DeviceHealthRow]] = None):
        super().__init__(code, description)
        self.device_health_row_list = device_health_row_list or []
