from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import File


class FileResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', file: Optional[File] = None):
        super().__init__(code, description)
        self.file = file or File()


class FileListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', file_list: Optional[List[File]] = None):
        super().__init__(code, description)
        self.file_list = file_list or []