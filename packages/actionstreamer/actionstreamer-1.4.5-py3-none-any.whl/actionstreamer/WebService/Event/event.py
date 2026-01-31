import json
from actionstreamer.CommonFunctions import send_signed_request, send_signed_request_long_poll
from actionstreamer.Result import StandardResult, EventWithNamesListResult, EventResult
from actionstreamer.Config import WebServiceConfig
from actionstreamer.CommonFunctions import get_exception_info
from actionstreamer.Model import EventWithNames, Event


def get_pending_event_list(ws_config: WebServiceConfig, device_serial: str) -> EventWithNamesListResult:

    event_with_names_list_result = EventWithNamesListResult()
    result = StandardResult()

    try:
        method = "POST"
        path = 'v1/event/list/pending'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        json_post_data = {
            "deviceName": device_serial
        }

        body = json.dumps(json_post_data)
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        if result.code == 200:
            json_dict = json.loads(result.description)
            event_with_names_list_result.event_with_names_list = [EventWithNames(**item) for item in json_dict]

    except Exception as ex:
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    event_with_names_list_result.code = result.code
    event_with_names_list_result.description = result.description

    return event_with_names_list_result


def get_pending_event_list_long_poll(ws_config: WebServiceConfig, device_serial: str, timeout: int = 62) -> EventWithNamesListResult:

    event_with_names_list_result = EventWithNamesListResult()
    result = StandardResult()

    try:
        method = "POST"
        path = 'v1/event/list/pending/longpoll'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        json_post_data = {
            "deviceName": device_serial
        }

        body = json.dumps(json_post_data)
        
        result = send_signed_request_long_poll(ws_config, method, url, path, headers, parameters, body, True, timeout)
        
        if result.code == 200:
            json_dict = json.loads(result.description)
            event_with_names_list_result.event_with_names_list = [EventWithNames(**item) for item in json_dict]

    except Exception as ex:
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    event_with_names_list_result.code = result.code
    event_with_names_list_result.description = result.description

    return event_with_names_list_result 


def dequeue_event(ws_config: WebServiceConfig, device_serial: str, agent_type: str) -> EventResult:

    event_result = EventResult()

    try:
        method = "POST"
        path = 'v1/event/dequeue'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        json_post_data = {
            "deviceName": device_serial,
            "deviceSerial": device_serial,
            "agentType": agent_type
        }

        body = json.dumps(json_post_data)
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        if result.code == 200:
            if result.description:
                json_dict = json.loads(result.description)
                event_result.event = Event(**json_dict)
            else:
                event_result.event = None

        event_result.code = result.code
        event_result.description = result.description

    except Exception as ex:
        event_result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        event_result.description = str(ex)

    return event_result 


def create_event(ws_config: WebServiceConfig, device_id: int, device_serial: str, agent_type: str, event_type: str, server_event: int = 0, event_parameters: str = '', priority: int = 1, max_attempts: int = 0, expiration_epoch: int = 0) -> StandardResult:

    result = StandardResult()

    try:
        method = "POST"
        path = 'v1/event'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        json_post_data = {
            "deviceID": device_id,
            "deviceSerial": device_serial,
            "agentType": agent_type,
            "eventType": event_type,
            "serverEvent": server_event,
            "eventParameters": event_parameters,
            "priority": priority,
            "maxAttempts": max_attempts,
            "expirationEpoch": expiration_epoch
        }

        body = json.dumps(json_post_data)
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
    except Exception as ex:
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    return result


def create_event_with_ids(ws_config: WebServiceConfig, device_id: int, device_serial: str, agent_type_id: int, event_type_id: int, server_event: int = 0, event_parameters: str = '', priority: int = 1, max_attempts: int = 0, expiration_epoch: int = 0) -> StandardResult:

    result = StandardResult()

    try:
        method = "POST"
        path = 'v1/event'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        json_post_data = {
            "deviceID": device_id,
            "deviceSerial": device_serial,
            "agentTypeID": agent_type_id,
            "eventTypeID": event_type_id,
            "serverEvent": server_event,
            "eventParameters": event_parameters,
            "priority": priority,
            "maxAttempts": max_attempts,
            "expirationEpoch": expiration_epoch
        }

        body = json.dumps(json_post_data)
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    return result


def get_event(ws_config: WebServiceConfig, event_id: int) -> EventResult:

    event_result = EventResult()
    result = StandardResult()

    try:
        method = "GET"
        path = 'v1/event/' + str(event_id)
        url = ws_config.base_url + path
        parameters: dict[str, str] = {}
        headers: dict[str, str] = {}
        body = ''
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        if result.code == 200:
            json_dict = json.loads(result.description)
            event_result.event = Event(**json_dict)

    except Exception as ex:
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    event_result.code = result.code
    event_result.description = result.description

    return event_result 


def update_event_progress(ws_config: WebServiceConfig, event_id: int, device_serial: str, percent_complete: float) -> StandardResult:

    result = StandardResult()

    try:
        method = "PATCH"
        path = 'v1/event/' + str(event_id) + '/progress'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        json_post_data = {
            "deviceName": device_serial,
            "deviceSerial": device_serial,
            "percentComplete": percent_complete
        }

        body = json.dumps(json_post_data)
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
    except Exception as ex:
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    return result


def update_event(ws_config: WebServiceConfig, event_id: int, event_status: int, result_string: str, process_id: int, tag_string: str ='', tag_number: int = 0, attempt_number: int = 1) -> StandardResult:

    result = StandardResult()

    try:
        method = "PUT"
        path = 'v1/event/' + str(event_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        json_post_data = {
            "eventStatus": event_status,
            "attemptNumber": attempt_number,
            "result": result_string,
            "processID": process_id,
            "tagString": tag_string,
            "tagNumber": tag_number
        }

        body = json.dumps(json_post_data)
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    return result


def update_event_with_progress(ws_config: WebServiceConfig, event_id: int, event_status: int, result_string: str, process_id: int, tag_string: str ='', tag_number: int = 0, percent_complete: float = 0, attempt_number: int = 1) -> StandardResult:

    result = StandardResult()

    try:
        method = "PUT"
        path = 'v1/event/' + str(event_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        json_post_data = {
            "eventStatus": event_status,
            "attemptNumber": attempt_number,
            "result": result_string,
            "processID": process_id,
            "percentComplete": percent_complete,
            "tagString": tag_string,
            "tagNumber": tag_number
        }

        body = json.dumps(json_post_data)
        
        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    return result