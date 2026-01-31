from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import Notification


class NotificationResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', notification: Optional[Notification] = None):
        super().__init__(code, description)
        self.notification = notification or Notification()


class NotificationListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', notification_list: Optional[List[Notification]] = None):
        super().__init__(code, description)
        self.notification_list = notification_list or []