from typing import Optional, List

from .standard_result import StandardResult
from actionstreamer.Model import VideoClip


class VideoClipResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', video_clip: Optional[VideoClip] = None):
        super().__init__(code, description)
        self.video_clip = video_clip or VideoClip()


class VideoClipListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', video_clip_list: Optional[List[VideoClip]] = None):
        super().__init__(code, description)
        self.video_clip_list = video_clip_list or []