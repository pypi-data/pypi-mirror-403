import json

from actionstreamer.Config import WebServiceConfig
from actionstreamer.Model import Package
from actionstreamer.Result import PackageResult, PackageListResult, StandardResult
from actionstreamer.CommonFunctions import send_signed_request, get_exception_info

def get_package(ws_config: WebServiceConfig, package_id: int) -> PackageResult:

    package_result = PackageResult()
    result = StandardResult()

    try:
        method = "GET"
        path = 'v1/package/' + str(package_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        result = send_signed_request(ws_config, method, url, path, headers, parameters)

        if result.code == 200:
            json_dict = json.loads(result.description)
            package_result.package = Package(**json_dict)

    except Exception as ex:        
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_package at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    package_result.code = result.code
    package_result.description = result.description

    return package_result


def get_package_list(ws_config: WebServiceConfig) -> PackageListResult:

    package_list_result = PackageListResult()
    result = StandardResult()

    try:
        method = "POST"
        path = 'v1/package/list'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        body = json.dumps({})

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

        if result.code == 200:
            json_dict = json.loads(result.description)
            package_list_result.package_list = [Package(**item) for item in json_dict]

    except Exception as ex:        
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_package_list at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    package_list_result.code = result.code
    package_list_result.description = result.description

    return package_list_result