import json
from typing import Any, TypeAlias


class DeviceHealth:

    extra_fields: dict[str, Any]

    def __init__(
        self,
        key: int = 0,
        user_id: int = 0,
        device_id: int = 0,
        health_date: str = '',
        health_json: str = '',
        creation_date: str = '',
        created_by: int = 0,
        last_modified_date: str = '',
        last_modified_by: int = 0,
        **kwargs: Any
    ):
        self.key = key
        self.user_id = user_id
        self.device_id = device_id
        self.health_date = health_date
        self.health_json = health_json
        self.creation_date = creation_date
        self.created_by = created_by
        self.last_modified_date = last_modified_date
        self.last_modified_by = last_modified_by

        camel_to_snake = {
            "userID": "user_id",
            "deviceID": "device_id",
            "healthDate": "health_date",
            "healthJSON": "health_json",
            "creationDate": "creation_date",
            "createdBy": "created_by",
            "lastModifiedDate": "last_modified_date",
            "lastModifiedBy": "last_modified_by",
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "key": self.key,
            "userID": self.user_id,
            "deviceID": self.device_id,
            "healthDate": self.health_date,
            "healthJSON": self.health_json,
            "creationDate": self.creation_date,
            "createdBy": self.created_by,
            "lastModifiedDate": self.last_modified_date,
            "lastModifiedBy": self.last_modified_by,
        }

    def to_json(self):
        return json.dumps(self.to_dict())


DeviceHealthList: TypeAlias = list[DeviceHealth]