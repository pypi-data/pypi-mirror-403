import json
from typing import Any
from datetime import datetime


class WifiConnection:

    extra_fields: dict[str, Any]

    def __init__(
            self,
            key: int = 0,
            user_id: int = 0,
            security_type: str = "",
            ssid: str = "",
            alias: str = "",
            password: str = "",
            priority: int = 0,
            creation_date: datetime = datetime.min,
            created_by: int = 0,
            last_modified_date: datetime = datetime.min,
            last_modified_by: int = 0,
            **kwargs: Any
    ):
        self.key = key
        self.user_id = user_id
        self.security_type = security_type
        self.ssid = ssid
        self.alias = alias
        self.password = password
        self.priority = priority
        self.creation_date = creation_date
        self.created_by = created_by
        self.last_modified_date = last_modified_date
        self.last_modified_by = last_modified_by

        camel_to_snake = {
            "key": "key",
            "userID": "user_id",
            "securityType": "security_type",
            "SSID": "ssid",
            "alias": "alias",
            "creationDate": "creation_date",
            "createdBy": "created_by",
            "lastModifiedDate": "last_modified_date",
            "lastModifiedBy": "last_modified_by"
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
            "securityType": self.security_type,
            "SSID": self.ssid,
            "alias": self.alias,
            "password": self.password,
            "priority": self.priority,
            "creationDate": self.creation_date.isoformat(),
            "createdBy": self.created_by,
            "lastModifiedDate": self.last_modified_date.isoformat(),
            "lastModifiedBy": self.last_modified_by
        }

    def to_json(self):
        return json.dumps(self.to_dict())
