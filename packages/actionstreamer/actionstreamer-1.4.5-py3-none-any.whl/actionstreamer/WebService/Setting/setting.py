import json

from actionstreamer.Config import WebServiceConfig
from actionstreamer.Result import StandardResult
from actionstreamer.CommonFunctions import send_signed_request, get_exception_info


def get_device_setting(ws_config: WebServiceConfig, device_id: int, setting_name: str) -> StandardResult:

    result = StandardResult()

    try:
        method = "GET"
        path = f"v1/devicesetting/device/{device_id}"
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = {"settingname": setting_name} 
        
        body = ""

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:        
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_device_setting at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    return result


def update_device_setting(ws_config: WebServiceConfig, device_id: int, setting_name: str, setting_value: str) -> StandardResult:

    result = StandardResult()

    try:
        method = "PUT"
        path = f"v1/devicesetting/device/{device_id}"
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        
        json_post_data = {"name":setting_name, "value":setting_value}

        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:        
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in update_device_setting at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    return result


def get_user_setting(ws_config: WebServiceConfig, setting_name: str) -> StandardResult:

    result = StandardResult()

    try:
        method = "GET"
        path = f"v1/usersetting"
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = {"settingname": setting_name} 
        
        body = ""

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:        
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_user_setting at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    return result
