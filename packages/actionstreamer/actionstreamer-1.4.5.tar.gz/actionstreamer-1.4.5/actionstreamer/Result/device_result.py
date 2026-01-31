from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import Device


class DeviceResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', device: Optional[Device] = None):
        super().__init__(code, description)
        self.device = device or Device()


class DeviceListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', device_list: Optional[List[Device]] = None):
        super().__init__(code, description)
        self.device_list = device_list or []
