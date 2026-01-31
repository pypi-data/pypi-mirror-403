import json


class StandardResult:
    def __init__(self, code: int = 0, description: str = ''):
        self.code = code
        self.description = description

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "description": self.description
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, description={self.description!r})"

    def __str__(self) -> str:
        return self.description
