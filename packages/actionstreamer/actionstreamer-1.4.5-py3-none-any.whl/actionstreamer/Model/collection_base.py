import json
from typing import Any, Optional
from enum import Enum
from .item_type import ItemType

class CollectionBase:

    extra_fields: dict[str, Any]

    def __init__(
        self,
        key: int = 0,
        collection_name: str = '',
        description: str = '',
        user_id: int = 0,
        item_type: Optional[Enum] = None,
        item_id: int = 0,
        parent_id: int = 0,
        creation_date: str = '',
        created_by: int = 0,
        last_modified_date: str = '',
        last_modified_by: int = 0,
        **kwargs: Any
    ):
        self.key = key
        self.collection_name = collection_name
        self.description = description
        self.user_id = user_id
        self.item_type = item_type
        self.item_id = item_id
        self.parent_id = parent_id
        self.creation_date = creation_date
        self.created_by = created_by
        self.last_modified_date = last_modified_date
        self.last_modified_by = last_modified_by

        camel_to_snake = {
            "collectionName": "collection_name",
            "description": "description",
            "userID": "user_id",
            "itemTypeID": "item_type",
            "itemID": "item_id",
            "parentID": "parent_id",
            "creationDate": "creation_date",
            "createdBy": "created_by",
            "lastModifiedDate": "last_modified_date",
            "lastModifiedBy": "last_modified_by",
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                value = kwargs.pop(camel_key)
                if snake_key == "item_type" and value is not None:
                    self.item_type = ItemType(value)
                else:
                    setattr(self, snake_key, value)

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "key": self.key,
            "collectionName": self.collection_name,
            "description": self.description,
            "userID": self.user_id,
            "itemTypeID": self.item_type.value if self.item_type else None,
            "itemID": self.item_id,
            "parentID": self.parent_id,
            "creationDate": self.creation_date,
            "createdBy": self.created_by,
            "lastModifiedDate": self.last_modified_date,
            "lastModifiedBy": self.last_modified_by,
        }

    def to_json(self):
        return json.dumps(self.to_dict())