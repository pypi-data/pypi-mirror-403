import json

from actionstreamer.Model import File
from actionstreamer.Result import StandardResult, FileResult
from actionstreamer.Config import WebServiceConfig
from actionstreamer.CommonFunctions import send_signed_request, get_exception_info


def create_file(ws_config: WebServiceConfig, device_serial: str, filename: str, file_size: int, sha256_hash: str) -> FileResult:

    """
    Create a file.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    device_serial (string): The device name.
    filename (string): The filename (no path information, just the name).
    file_size (int): The file size in bytes.
    sha256_hash (string): The SHA256 hash for the file.
    
    Returns:
    response_code: The API HTTP response code.
    response_string: The API HTTP response body
    signed_url: The URL to upload the file to.
    file_id: The ID for the newly generated file.
    """

    file_result = FileResult()

    try:
        json_post_data = {"deviceName":device_serial, "filename":filename, "fileSize":file_size, "sHA256Hash":sha256_hash, "deviceSerial":device_serial}

        method = "POST"
        path = 'v1/file'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        file_result.code = result.code
        file_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            file_result.file = File(**json_dict)
            
            file_result.code = result.code
            file_result.description = result.description

    except Exception as ex:
        
        ex_filename, line_number = get_exception_info()

        if ex_filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        file_result.code = -1
        file_result.description = "Exception in create_file.  " + str(ex)

    return file_result


def create_temp_file(ws_config: WebServiceConfig, device_serial: str, filename: str, file_size: int, sha256_hash: str) -> FileResult:

    """
    Create a temp file.  This file will be deleted from S3 after 24 hours.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    device_serial (string): The device serial number.
    filename (string): The filename (no path information, just the name).
    file_size (int): The file size in bytes.
    sha256_hash (string): The SHA256 hash for the file.
    
    Returns:
    response_code: The API HTTP response code.
    response_string: The API HTTP response body
    signed_url: The URL to upload the file to.
    file_id: The ID for the newly generated file.
    """

    file_result = FileResult()

    try:
        json_post_data = {"deviceName":device_serial, "filename":filename, "fileSize":file_size, "sHA256Hash":sha256_hash, "deviceSerial":device_serial}

        method = "POST"
        path = 'v1/file/temp'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        file_result.code = result.code
        file_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            file_result.file = File(**json_dict)
            
            file_result.code = result.code
            file_result.description = result.description

    except Exception as ex:        
        ex_filename, line_number = get_exception_info()
        if ex_filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        file_result.code = -1
        file_result.description = "Exception in create_file"

    return file_result


def update_file_upload_success(ws_config: WebServiceConfig, device_serial: str, file_id: int) -> StandardResult:

    result = StandardResult()

    try:
        json_post_data = {'deviceSerial':device_serial}

        method = "POST"
        path = 'v1/file/success/' + str(file_id)
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
        result.description = "Exception in update_file_upload_success"

    return result


def get_file(ws_config: WebServiceConfig, file_id: int) -> FileResult:

    file_result = FileResult()

    try:

        method = "GET"
        path = 'v1/file/' + str(file_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        result = send_signed_request(ws_config, method, url, path, headers, parameters)
        file_result.code = result.code
        file_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            file_result.file = File(**json_dict)
            
            file_result.code = result.code
            file_result.description = result.description

    except Exception as ex:
        
        file_result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_file at line {line_number} in {filename}")
        print(ex)
        file_result.description = str(ex)

    return file_result