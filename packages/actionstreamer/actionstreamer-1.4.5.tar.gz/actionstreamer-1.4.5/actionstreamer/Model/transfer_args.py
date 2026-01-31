import json
from .event_args import EventArgs
from typing import Any


class TransferArgs(EventArgs):

    extra_fields: dict[str, Any]

    def __init__(
        self,
        file_id: int = 0,
        item_type_id: int = 0,
        object_id: int = 0,
        local_file_path: str = '',
        remote_filename: str = '',
        remote_folder_path: str = '',
        url: str = '',
        action: str = '',
        attempt_number: int = 0,
        max_attempts: int = 0,
        first_attempt_start_time: int = 0,
        max_time_to_try_in_seconds: int = 0,
        **kwargs: Any
    ):
        self.file_id = file_id
        self.item_type_id = item_type_id
        self.object_id = object_id
        self.local_file_path = local_file_path
        self.remote_filename = remote_filename
        self.remote_folder_path = remote_folder_path
        self.url = url
        self.action = action
        self.attempt_number = attempt_number
        self.max_attempts = max_attempts
        self.first_attempt_start_time = first_attempt_start_time
        self.max_time_to_try_in_seconds = max_time_to_try_in_seconds

        camel_to_snake = {
            "fileID": "file_id",
            "itemTypeID": "item_type_id",
            "objectID": "object_id",
            "localFilePath": "local_file_path",
            "remoteFilename": "remote_filename",
            "remoteFolderPath": "remote_folder_path",
            "attemptNumber": "attempt_number",
            "maxAttempts": "max_attempts",
            "firstAttemptStartTime": "first_attempt_start_time",
            "maxTimeToTryInSeconds": "max_time_to_try_in_seconds"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "fileID": self.file_id,
            "itemTypeID": self.item_type_id,
            "objectID": self.object_id,
            "localFilePath": self.local_file_path,
            "remoteFilename": self.remote_filename,
            "remoteFolderPath": self.remote_folder_path,
            "url": self.url,
            "action": self.action,
            "attemptNumber": self.attempt_number,
            "maxAttempts": self.max_attempts,
            "firstAttemptStartTime": self.first_attempt_start_time,
            "maxTimeToTryInSeconds": self.max_time_to_try_in_seconds
        }

    def to_json(self):
        return json.dumps(self.to_dict())
