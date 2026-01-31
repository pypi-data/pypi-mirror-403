import json
from typing import Any

from actionstreamer.Model import DeviceHealth, DeviceHealthRow
from actionstreamer.Result import StandardResult, IntegerResult, DeviceHealthListResult, DeviceHealthRowListResult
from actionstreamer.Config import WebServiceConfig
from actionstreamer.CommonFunctions import send_signed_request, get_exception_info


def create_health(ws_config: WebServiceConfig, device_serial: str, health_json: str) -> IntegerResult:
    
    integer_result = IntegerResult()
    result = StandardResult()

    try:
        method = "POST"
        path = 'v1/devicehealth'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = None

        json_post_data = {
            "deviceName": device_serial,
            "deviceSerial": device_serial,
            "healthJSON": health_json
        }

        body = json.dumps(json_post_data)
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        if result.code == 200:
            json_dict = json.loads(result.description)

            integer_result.value = json_dict.get("deviceHealthID", 0)

    except Exception as ex:
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

    integer_result.code = result.code
    integer_result.description = result.description

    return integer_result


def update_health(ws_config: WebServiceConfig, device_serial: str, health_json: str) -> IntegerResult:

    integer_result = IntegerResult()
    result = StandardResult()

    try:
        method = "POST"
        path = 'v1/devicehealth/updatelatest'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = None

        json_post_data = {
            "deviceName": device_serial,
            "deviceSerial": device_serial,
            "healthJSON": health_json
        }

        body = json.dumps(json_post_data)
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        if result.code == 200:
            json_dict = json.loads(result.description)

            integer_result.value = json_dict.get("deviceHealthID", 0)

    except Exception as ex:
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

    integer_result.code = result.code
    integer_result.description = result.description

    return integer_result


def get_device_health_list(ws_config: WebServiceConfig, device_id: int, start_epoch: int, end_epoch: int, count: int = 0, order: str = 'desc') -> DeviceHealthListResult:

    result = StandardResult()
    device_health_list_result = DeviceHealthListResult()

    try:
        method = "POST"
        path = 'v1/devicehealth/list'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = None
        
        json_post_data = {
            "deviceID": device_id,
            "startEpoch": start_epoch,
            "endEpoch": end_epoch,
            "count": count,
            "order": order
        }

        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        device_health_list_result.code = result.code
        device_health_list_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            device_health_list_result.device_health_list = [DeviceHealth(**item) for item in json_dict]

    except Exception as ex:        
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_device_health_list at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    device_health_list_result.code = result.code
    device_health_list_result.description = result.description

    return device_health_list_result


def get_device_health_row_list(ws_config: WebServiceConfig, online_only: bool = True) -> DeviceHealthRowListResult:

    device_health_row_list_result = DeviceHealthRowListResult()
    device_health_row_list: list[DeviceHealthRow] = []

    try:
        status = "online" if online_only else "all"
        query_params: dict[str, str] = {"status": status}

        method = "GET"
        path = "v1/device/list/health"
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        body = ""

        result = send_signed_request(ws_config, method, url, path, headers, query_params, body)

        parsed_json: list[dict[str, Any]] = json.loads(result.description)
        device_health_row_list = [DeviceHealthRow.from_mapping(row) for row in parsed_json]

        device_health_row_list_result = DeviceHealthRowListResult(result.code, result.description, device_health_row_list)

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_device_health_row_list at line {line_number} in {filename}")
        device_health_row_list_result = DeviceHealthRowListResult(-1, str(ex), None)

    return device_health_row_list_result
