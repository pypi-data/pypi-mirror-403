import json
from .event_args import EventArgs
from typing import Any


class SendUDPAudioArgs(EventArgs):

    extra_fields: dict[str, Any]

    def __init__(
        self,
        receiver_ip_address: str = '',
        port: int = 0,
        receiver_device_id: int = 0,
        **kwargs: Any
    ):
        self.receiver_ip_address = receiver_ip_address
        self.port = port
        self.receiver_device_id = receiver_device_id

        camel_to_snake = {
            "receiverIPAddress": "receiver_ip_address",
            "receiverDeviceID": "receiver_device_id"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "receiverIPAddress": self.receiver_ip_address,
            "port": self.port,
            "receiverDeviceID": self.receiver_device_id
        }

    def to_json(self):
        return json.dumps(self.to_dict())
