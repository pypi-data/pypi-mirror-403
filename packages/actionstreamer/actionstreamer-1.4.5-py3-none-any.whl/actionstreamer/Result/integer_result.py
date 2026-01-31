from typing import Optional, List

from .standard_result import StandardResult


class IntegerResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', value: Optional[int] = None):
        super().__init__(code, description)
        self.value = value if value is not None else 0


class IntegerListResult(StandardResult):
    def __init__(self, code: int = 0, description: str = '', value_list: Optional[List[int]] = None):
        super().__init__(code, description)
        self.value_list = value_list if value_list is not None else []
