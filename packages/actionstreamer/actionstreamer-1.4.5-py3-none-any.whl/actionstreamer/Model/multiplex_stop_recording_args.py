import json
from .event_args import EventArgs
from typing import Any


class MultiplexStopRecordingArgs(EventArgs):

    extra_fields: dict[str, Any]

    def __init__(
            self, 
            device_id: int = 0, 
            **kwargs: Any
    ):
        self.device_id = device_id

        if "deviceID" in kwargs:
            self.device_id = kwargs.pop("deviceID")

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "deviceID": self.device_id
        }

    def to_json(self):
        return json.dumps(self.to_dict())
