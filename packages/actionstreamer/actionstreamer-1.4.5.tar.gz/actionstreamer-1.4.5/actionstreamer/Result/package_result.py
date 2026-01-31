from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import Package


class PackageResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', package: Optional[Package] = None):
        super().__init__(code, description)
        self.package = package or Package()


class PackageListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', package_list: Optional[List[Package]] = None):
        super().__init__(code, description)
        self.package_list = package_list or []