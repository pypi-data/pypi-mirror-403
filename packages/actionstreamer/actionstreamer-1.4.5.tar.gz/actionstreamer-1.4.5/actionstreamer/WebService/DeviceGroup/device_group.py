import json

from actionstreamer.Result import StandardResult, DeviceGroupResult
from actionstreamer.Model import DeviceGroup
from actionstreamer.Config import WebServiceConfig
from actionstreamer.CommonFunctions import send_signed_request, get_exception_info


def create_device_group(ws_config: WebServiceConfig, group_name: str,) -> DeviceGroupResult:

    """
    Create a device group.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    group_name (string): The device group name.
    
    Returns:
    device_group_result: The result object of the attempted action. It contains the following fields {code: int, description: str, device_group: DeviceGroup}
    """

    device_group_result = DeviceGroupResult()

    try:
        json_post_data = {"value":group_name}

        method = "POST"
        path = 'v1/devicegroup'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        device_group_result.code = result.code
        device_group_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            device_group_result.device_group = DeviceGroup(**json_dict)
            
    except Exception as ex:        
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        device_group_result.code = -1
        device_group_result.description = "Exception in create_device_group"

    return device_group_result


def add_device_to_group(ws_config: WebServiceConfig, device_group_id: int, device_id: int) -> StandardResult:
    """
    Add a device to a group.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    device_group_id (int): The device group id to add a device to.
    device_id (int): The device id to be added to the group.
    
    Returns:
    result: The result object of the attempted action.  It contains the following fields {code: int, description: str}
    """

    result = StandardResult()

    try:
        method = "POST"
        path = f'v1/devicegroup/{device_group_id}/device/{device_id}'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = ""

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:        
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.code = -1
        result.description = "Exception in add_device_to_group"

    return result


def get_device_group(ws_config: WebServiceConfig, device_group_name: str) -> DeviceGroupResult:
    
    device_group_result = DeviceGroupResult()
    result = StandardResult()
    try:
        method = "GET"
        path = 'v1/devicegroup'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        
        json_post_data = {"value":device_group_name}
        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

        if result.code == 200:
            json_dict = json.loads(result.description)
            device_group_result.device_group = DeviceGroup(**json_dict)

    except Exception as ex:
        
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_device_group at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    device_group_result.code = result.code
    device_group_result.description = result.description

    return device_group_result


def get_device_group_by_id(ws_config: WebServiceConfig, device_group_id: int) -> DeviceGroupResult:

    device_group_result = DeviceGroupResult()
    result = StandardResult()

    try:
        method = "GET"
        path = 'v1/devicegroup/' + str(device_group_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        result = send_signed_request(ws_config, method, url, path, headers, parameters, '')

        if result.code == 200:
            json_dict = json.loads(result.description)
            device_group_result.device_group = DeviceGroup(**json_dict)

    except Exception as ex:        
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_device_group_by_id at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    device_group_result.code = result.code
    device_group_result.description = result.description

    return device_group_result