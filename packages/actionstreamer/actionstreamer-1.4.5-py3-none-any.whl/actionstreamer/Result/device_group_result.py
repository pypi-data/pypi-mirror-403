from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import DeviceGroup


class DeviceGroupResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', device_group: Optional[DeviceGroup] = None):
        super().__init__(code, description)
        self.device_group = device_group or DeviceGroup()


class DeviceGroupListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', device_group_list: Optional[List[DeviceGroup]] = None):
        super().__init__(code, description)
        self.device_group_list = device_group_list or []
