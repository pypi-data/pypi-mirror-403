import json
from typing import Any


class EventPreset:

    extra_fields: dict[str, Any]

    def __init__(
        self,
        key: int = 0,
        event_preset_name: str = '',
        user_id: int = 0,
        device_id: int = 0,
        device_group_id: int = 0,
        agent_type_id: int = 0,
        agent_id: int = 0,
        event_type_id: int = 0,
        event_status: int = 0,
        event_parameters: str = "",
        process_id: int = 0,
        result: str = "",
        percent_complete: int = 0,
        priority: int = 1,
        expiration_epoch: int = 0,
        attempt_number: int = 0,
        max_attempts: int = 5,
        checkout_token: str = "",
        tag_string: str = "",
        tag_number: int = 0,
        creation_date: str = "", 
        created_by: int = 0,
        last_modified_date: str = "",
        last_modified_by: int = 0,
        **kwargs: Any
    ):
        self.key = key
        self.event_preset_name = event_preset_name
        self.user_id = user_id
        self.device_id = device_id
        self.device_group_id = device_group_id
        self.agent_type_id = agent_type_id
        self.agent_id = agent_id
        self.event_type_id = event_type_id
        self.event_status = event_status
        self.event_parameters = event_parameters
        self.process_id = process_id
        self.result = result
        self.percent_complete = percent_complete
        self.priority = priority
        self.expiration_epoch = expiration_epoch
        self.attempt_number = attempt_number
        self.max_attempts = max_attempts
        self.checkout_token = checkout_token
        self.tag_string = tag_string
        self.tag_number = tag_number
        self.creation_date = creation_date
        self.created_by = created_by
        self.last_modified_date = last_modified_date
        self.last_modified_by = last_modified_by


        camel_to_snake = {
            "eventPresetName": "event_preset_name",
            "userID": "user_id",
            "deviceID": "device_id",
            "deviceGroupID": "device_group_id",
            "agentTypeID": "agent_type_id",
            "agentID": "agent_id",
            "eventTypeID": "event_type_id",
            "eventStatus": "event_status",
            "eventParameters": "event_parameters",
            "processID": "process_id",
            "percentComplete": "percent_complete",
            "expirationEpoch": "expiration_epoch",
            "attemptNumber": "attempt_number",
            "maxAttempts": "max_attempts",
            "checkoutToken": "checkout_token",
            "tagString": "tag_string",
            "tagNumber": "tag_number",
            "creationDate": "creation_date",
            "lastModifiedDate": "last_modified_date",
            "lastModifiedBy": "last_modified_by",
            "createdBy": "created_by"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "key" : self.key,
            "eventPresetName" : self.event_preset_name,
            "userID" : self.user_id,
            "deviceID" : self.device_id,
            "deviceGroupID" : self.device_group_id ,
            "agentTypeID" : self.agent_type_id,
            "agentID" : self.agent_id,
            "eventTypeID" : self.event_type_id,
            "eventStatus" : self.event_status,
            "eventParameters" : self.event_parameters,
            "processID" : self.process_id,
            "result" : self.result,
            "percentComplete" : self.percent_complete,
            "priority" : self.priority,
            "expirationEpoch" : self.expiration_epoch,
            "attemptNumber" : self.attempt_number,
            "maxAttempts" : self.max_attempts,
            "checkoutToken" : self.checkout_token,
            "tagString" : self.tag_string,
            "tagNumber" : self.tag_number,
            "creationDate" : self.creation_date,
            "createdBy" : self.created_by,
            "lastModifiedDate" : self.last_modified_date,
            "lastModifiedBy" : self.last_modified_by,
        } 

    def to_json(self):
        return json.dumps(self.to_dict())
