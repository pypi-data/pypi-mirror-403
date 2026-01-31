from datetime import datetime
import json

class TagListForDeviceList:
    def __init__(
        self,
        device_id_list: list[int] = [],
        tag_id_list: list[int] = [],
        start_epoch: int = 0,
        end_epoch: int = int(datetime.now().timestamp()),
        count: int = 0,
        order: str = 'desc',
    ):
        self.device_id_list = device_id_list
        self.tag_id_list = tag_id_list
        self.start_epoch = start_epoch
        self.end_epoch = end_epoch
        self.count = count
        self.order = order

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "deviceIDList": self.device_id_list,
            "tagIDList": self.tag_id_list,
            "startEpoch": self.start_epoch,
            "endEpoch": self.end_epoch,
            "count": self.count,
            "order": self.order,
        }
    
    def to_json(self):
        return json.dumps(self.to_dict())