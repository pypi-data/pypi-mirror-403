import json
from typing import Any

class WorkflowPreset:

    device_id: int = 0
    event_preset_id: int = 0

    extra_fields: dict[str, Any]

    def __init__(self, device_id: int = 0, event_preset_id: int = 0, **kwargs: Any):
        
        self.device_id = device_id
        self.event_preset_id = event_preset_id

        camel_to_snake = {
            "deviceID": "device_id",
            "eventPresetID": "event_preset_id"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "deviceID": self.device_id,
            "eventPresetID": self.event_preset_id
        }

    def to_json(self):
        return json.dumps(self.to_dict())
