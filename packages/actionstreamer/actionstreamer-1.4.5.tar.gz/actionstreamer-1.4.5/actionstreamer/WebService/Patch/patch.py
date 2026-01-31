import json
from typing import List

from actionstreamer.Model import PatchOperation


def add_patch_operation(operation_list: List[PatchOperation], field_name: str, value: str) -> None:
    operation_list.append(PatchOperation(field_name=field_name, value=value))


def generate_patch_json(operation_list: list[PatchOperation]) -> str:
    operations_str: List[dict[str, str]] = [operation.to_dict() for operation in operation_list]
    return json.dumps(operations_str)