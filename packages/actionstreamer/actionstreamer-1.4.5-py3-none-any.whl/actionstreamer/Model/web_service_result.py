import json
from typing import Any

class WebServiceResult:

    extra_fields: dict[str, Any]

    def __init__(self, code: int = 0, description: str = '', http_response_code: int = 0, http_response_string: str = '', json_data: dict[str, Any] | None = None, **kwargs: Any):
        self.code = code
        self.description = description
        self.http_response_code = http_response_code
        self.http_response_string = http_response_string
        self.json_data = json_data

        camel_to_snake = {
            "httpResponseCode": "http_response_code",
            "httpResponseString": "http_response_string",
            "jsonData": "json_data"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "description": self.description,
            "httpResponseCode": self.http_response_code,
            "httpResponseString": self.http_response_string,
            "jsonData": self.json_data
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
