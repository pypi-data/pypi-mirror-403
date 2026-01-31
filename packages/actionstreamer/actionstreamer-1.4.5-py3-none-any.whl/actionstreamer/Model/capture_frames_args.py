import json
from .event_args import EventArgs
from typing import Any

class CaptureFramesArgs(EventArgs):

    extra_fields: dict[str, Any]

    def __init__(
        self,
        height: int = 1920,
        width: int = 1080,
        fps: float = 30,
        rotation_degrees: int = 0,
        **kwargs: Any
    ):
        self.height = height
        self.width = width
        self.fps = fps
        self.rotation_degrees = rotation_degrees

        camel_to_snake = {
            "rotationDegrees": "rotation_degrees"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "height": self.height,
            "width": self.width,
            "fps": self.fps,
            "rotationDegrees": self.rotation_degrees
        }

    def to_json(self):
        return json.dumps(self.to_dict())
