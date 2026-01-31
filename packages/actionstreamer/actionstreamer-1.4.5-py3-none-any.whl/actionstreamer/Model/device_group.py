from .item_type import ItemType
from .collection_base import CollectionBase
from typing import Any

class DeviceGroup(CollectionBase):

    ITEM_TYPE = ItemType.Collection

    extra_fields: dict[str, Any]

    def __init__(
        self,
        collection_name: str = '',
        description: str = '',
        user_id: int = 0,
        parent_id: int = 0,
        **kwargs: Any
    ):
        super().__init__(
            collection_name=collection_name,
            description=description,
            user_id=user_id,
            parent_id=parent_id,
            item_type=self.ITEM_TYPE,
            **kwargs
        )