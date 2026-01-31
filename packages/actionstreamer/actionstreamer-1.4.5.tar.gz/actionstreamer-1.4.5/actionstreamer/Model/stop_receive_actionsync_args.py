import json
from .event_args import EventArgs
from typing import Any


class StopReceiveActionSyncArgs(EventArgs):

    extra_fields: dict[str, Any]

    def __init__(
            self, 
            sender_ip: str = '',
            sender_port: int = 0,
            sender_device_id: int = 0,
            **kwargs: Any
    ):
        self.sender_ip = sender_ip
        self.sender_port = sender_port
        self.sender_device_id = sender_device_id

        camel_to_snake = {
            "senderIP": "sender_ip",
            "senderPort": "sender_port",
            "senderDeviceID" : "sender_device_id"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "senderIP": self.sender_ip,
            "senderPort": self.sender_port,
            "senderDeviceID": self.sender_device_id
        }

    def to_json(self):
        return json.dumps(self.to_dict())
