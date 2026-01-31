import json
from typing import Any


class Tag:

    extra_fields: dict[str, Any]

    def __init__(
        self,
        key: int = 0,
        tag_name: str = '',
        creation_date: str = '',
        created_by: int = 0,
        last_modified_date: str = '',
        last_modified_by: int = 0,
        **kwargs: Any
    ):
        self.key = key
        self.tag_name = tag_name
        self.creation_date = creation_date
        self.created_by = created_by
        self.last_modified_date = last_modified_date
        self.last_modified_by = last_modified_by

        camel_to_snake = {
            "tagName": "tag_name",
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
            "tagName": self.tag_name,
            "creationDate": self.creation_date,
            "createdBy": self.created_by,
            "lastModifiedDate": self.last_modified_date,
            "lastModifiedBy": self.last_modified_by,
        }

    def to_json(self):
        return json.dumps(self.to_dict())
