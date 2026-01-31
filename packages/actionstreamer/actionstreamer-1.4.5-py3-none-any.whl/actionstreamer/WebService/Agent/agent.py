import json
from actionstreamer.CommonFunctions import send_signed_request
from actionstreamer.Result import StandardResult
from actionstreamer.Config import WebServiceConfig
from actionstreamer.CommonFunctions import get_exception_info

def register_agent(ws_config: WebServiceConfig, device_serial: str, agent_type: str, agent_version: str, agent_index: int, process_id: int) -> StandardResult:

    result = StandardResult()

    try:        
        json_post_data = {"deviceName":device_serial, "agentType":agent_type, "agentVersion":agent_version, "agentIndex":agent_index, "processID":process_id}

        method = "POST"
        path = 'v1/agent'
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
        result.description = "Exception in RegisterAgent"

    return result
