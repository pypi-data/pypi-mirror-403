from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import LogMessage


class LogMessageResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', log_message: Optional[LogMessage] = None):
        super().__init__(code, description)
        self.log_message = log_message or LogMessage()


class LogMessageListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', log_message_list: Optional[List[LogMessage]] = None):
        super().__init__(code, description)
        self.log_message_list = log_message_list or []