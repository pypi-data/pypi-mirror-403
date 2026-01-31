import json
from .event_args import EventArgs
from typing import Any


class ReceiveUDPAudioArgs(EventArgs):

    extra_fields: dict[str, Any]

    def __init__(
        self,
        sender_device_id: int = 0,
        port: int = 0,
        **kwargs: Any
    ):
        self.sender_device_id = sender_device_id
        self.port = port

        camel_to_snake = {
            "senderDeviceID": "sender_device_id"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "senderDeviceID": self.sender_device_id,
            "port": self.port
        }

    def to_json(self):
        return json.dumps(self.to_dict())
