import datetime
import json

from actionstreamer.Model import LogMessage
from actionstreamer.Result import LogMessageResult
from actionstreamer.Config import LogConfig
from actionstreamer.CommonFunctions import send_signed_request, get_exception_info, log_to_console as print_to_console


def create_log_message(log_config: LogConfig, message: str, log_to_console: bool = True) -> LogMessageResult:

    log_message_result = LogMessageResult()

    try:
        if (log_to_console):
            agent_name = str(log_config.agent_type) + "Agent:" + str(log_config.agent_index) + "_" + str(log_config.agent_version)
            print_to_console(message, agent_name)

        utc_now = datetime.datetime.now(datetime.timezone.utc)
        post_data = {"deviceName": log_config.device_serial, "agentType": log_config.agent_type, "agentVersion": log_config.agent_version, "agentIndex": log_config.agent_index, "processID": log_config.process_id, "message": message, "logDate": str(utc_now), "deviceSerial": log_config.device_serial}

        method = "POST"
        path = 'v1/logmessage'
        url = log_config.ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = json.dumps(post_data)

        result = send_signed_request(log_config.ws_config, method, url, path, headers, parameters, body)
        log_message_result.code = result.code
        log_message_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            log_message_result.log_message = LogMessage(**json_dict)
            
            log_message_result.code = result.code
            log_message_result.description = result.description

    except Exception as ex:        
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        log_message_result.code = -1
        log_message_result.description = "Exception in create_log_message"

    return log_message_result