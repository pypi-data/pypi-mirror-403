import json
from actionstreamer.CommonFunctions import send_signed_request
from actionstreamer.Result import StandardResult, DeviceResult
from actionstreamer.Config import WebServiceConfig
from actionstreamer.CommonFunctions import get_exception_info
from actionstreamer.Model import Device


def create_device(ws_config: WebServiceConfig, device: Device) -> DeviceResult:

    device_result = DeviceResult()

    try:
        method = "POST"
        path = 'v1/device'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = json.dumps(device.to_dict())

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

        device_result.code = result.code
        device_result.description = result.description

        if result.code == 200:
            json_dict = json_dict = json.loads(result.description)
            device_result.device = Device(**json_dict)

    except Exception as ex:        
        device_result.code = -1
        filename, line_number = get_exception_info()

        if filename is not None and line_number is not None:
            print(f"Exception occurred in create_device at line {line_number} in {filename}")

        print(ex)
        device_result.description = str(ex)

    return device_result


def device_ready(ws_config: WebServiceConfig, device_serial: str, agent_type: str, agent_version: str, agent_index: int, process_id: int) -> StandardResult:

    result = StandardResult()

    try:        
        json_post_data = {"deviceName":device_serial, "agentType":agent_type, "agentVersion":agent_version, "agentIndex":agent_index, "processID":process_id, "deviceSerial":device_serial}

        method = "POST"
        path = 'v1/device/ready'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = json.dumps(json_post_data)
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:        
        filename, line_number = get_exception_info()

        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")

        print(ex)
        result.code = -1
        result.description = "Exception in device_ready"

    return result


def get_device(ws_config: WebServiceConfig, device_name: str) -> DeviceResult:
    
    # The endpoint for this function checks first by device serial, then by friendly name.
    device_result = DeviceResult()
    result = StandardResult()

    try:
        json_post_data = {"deviceName":device_name}

        method = "POST"
        path = 'v1/device/name'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        
        json_post_data = {
            "deviceName": device_name
        }

        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

        if result.code == 200:
            json_dict = json.loads(result.description)
            device_result.device = Device(**json_dict)

    except Exception as ex:        
        result.code = -1
        filename, line_number = get_exception_info()

        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_device at line {line_number} in {filename}")

        print(ex)
        result.description = str(ex)

    device_result.code = result.code
    device_result.description = result.description

    return device_result


def get_device_by_id(ws_config: WebServiceConfig, device_id: int) -> DeviceResult:

    device_result = DeviceResult()
    result = StandardResult()

    try:
        method = "GET"
        path = 'v1/device/' + str(device_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        result = send_signed_request(ws_config, method, url, path, headers, parameters, '')

        if result.code == 200:
            json_dict = json.loads(result.description)
            device_result.device = Device(**json_dict)

    except Exception as ex:        
        result.code = -1
        filename, line_number = get_exception_info()

        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_device_by_id at line {line_number} in {filename}")

        print(ex)
        result.description = str(ex)

    device_result.code = result.code
    device_result.description = result.description

    return device_result


def update_device(ws_config: WebServiceConfig, device: Device) -> StandardResult:

    result = StandardResult()

    try:
        method = "PUT"
        path = f'v1/device/{device.key}'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = json.dumps(device.to_dict())

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        result.code = -1
        filename, line_number = get_exception_info()

        if filename is not None and line_number is not None:
            print(f"Exception occurred in update_device at line {line_number} in {filename}")
        print(ex)

        result.description = str(ex)

    return result


def set_device_run_analytics(ws_config: WebServiceConfig, device_id: int, run_analytics: int) -> StandardResult:
    """
    Update a device.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    device_id (int): device id of the device we are patching.
    run_analytics (int): value to set RunAnalytics to
    
    Returns:
    ws_result: The result object of the attempted action. It is comprised of the following fields {code: int, description: str, http_response_code: int, http_response_string: str, json_data: str}
    """
    
    result = StandardResult()

    try:
        method = "POST"
        path = f'v1/device/{device_id}/runanalytics/{run_analytics}'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = ''

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        result.code = -1
        filename, line_number = get_exception_info()

        if filename is not None and line_number is not None:
            print(f"Exception occurred in set_device_run_analytics at line {line_number} in {filename}")
        print(ex)

        result.description = str(ex)

    return result