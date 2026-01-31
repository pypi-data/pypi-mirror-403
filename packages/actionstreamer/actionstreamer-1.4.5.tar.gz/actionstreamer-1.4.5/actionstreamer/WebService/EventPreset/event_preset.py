import json

from actionstreamer.Result import StandardResult, EventPresetResult
from actionstreamer.Model import EventArgs, CreateEventPreset, EventType, EventPreset
from actionstreamer.Config import WebServiceConfig
from actionstreamer.CommonFunctions import send_signed_request, get_exception_info


def run_event_preset(ws_config: WebServiceConfig, event_preset_id: int) -> StandardResult:

    result = StandardResult()

    try:
        method = "POST"
        path = 'v1/eventpreset/run/' + str(event_preset_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        json_post_data = {}
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


def create_event_preset(ws_config: WebServiceConfig, device_id: int, event_type: str, event_preset_name: str, agent_type: str, event_parameters: EventArgs, priority: int = 1, max_attempts: int = 5, expiration_epoch: int = 0, device_group_id: int = 0) -> EventPresetResult:

    event_parameters_json: str = ''
    event_preset_object = CreateEventPreset(device_id, agent_type, event_type, event_parameters_json, event_preset_name, priority, max_attempts, expiration_epoch, device_group_id)

    result = StandardResult()
    event_preset_result = EventPresetResult()

    try:
        method = "POST"
        path = 'v1/eventpreset/'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        # Set the event parameters based on the event type.
        
        if event_type == f'Video_{EventType.Video.Start_recording.name}':
           event_parameters_json = event_parameters.to_json()

        elif event_type == f'Video_{EventType.Video.Stop_recording.name}':
            event_parameters_json = ''

        elif event_type == f'Video_{EventType.Video.Start_RTMP.name}':
            event_parameters_json = event_parameters.to_json()

        elif event_type == f'Video_{EventType.Video.Stop_RTMP.name}':
            event_parameters_json = ''

        elif event_type == f'Video_{EventType.Video.Join_conference.name}':
            event_parameters_json = event_parameters.to_json()

        elif event_type == f'Video_{EventType.Video.Leave_conference.name}':
            event_parameters_json = ''

        elif event_type == f'Video_{EventType.Video.Start_send_ActionSync.name}':
            event_parameters_json = event_parameters.to_json()
        
        elif event_type == f'Video_{EventType.Video.Start_receive_ActionSync.name}':
            event_parameters_json = event_parameters.to_json()
        
        elif event_type == f'Video_{EventType.Video.Start_receive_ActionSync_multiplex.name}':
            event_parameters_json = event_parameters.to_json()
        
        elif event_type == f'Video_{EventType.Video.Stop_receive_ActionSync.name}':
            event_parameters_json = event_parameters.to_json()

        elif event_type == f'Video_{EventType.Video.Multiplex_join_conference.name}':
            event_parameters_json = event_parameters.to_json()
        
        elif event_type == f'Video_{EventType.Video.Multiplex_leave_conference.name}':
            event_parameters_json = event_parameters.to_json()

        elif event_type == f'Video_{EventType.Video.Stop_receive_UDP_audio.name}':
            event_parameters_json = event_parameters.to_json()

        elif event_type == f'Video_{EventType.Video.Start_receive_UDP_audio.name}':
            event_parameters_json = event_parameters.to_json()

        elif event_type == f'Workflow_{EventType.Workflow.Event_preset_workflow.name}':
            event_parameters_json = event_parameters.to_json()

        elif event_type == f'Video_{EventType.Video.Start_send_UDP_audio.name}':
            event_parameters_json = event_parameters.to_json()

        elif event_type == f'Video_{EventType.Video.Stop_send_UDP_audio.name}':
            event_parameters_json = event_parameters.to_json()

        else:
            raise ValueError('Invalid event type')

        event_preset_object.event_parameters = event_parameters_json

        body = json.dumps(event_preset_object.to_dict())

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

        if result.code == 200:
            json_dict = json_dict = json.loads(result.description)
            event_preset_result.event_preset = EventPreset(**json_dict)
            
            event_preset_result.code = result.code
            event_preset_result.description = result.description

    except Exception as ex:        
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.code = -1
        result.description = "Exception in create_event_preset. Line number " + str(line_number)

    event_preset_result.code = result.code
    event_preset_result.description = result.description

    return event_preset_result 


def set_startup_preset(ws_config: WebServiceConfig, event_preset_id: int, offline_preset: bool = False, device_id: int = 0, device_group_id: int = 0) -> StandardResult:

    # If device_group_id is set, device_id will be ignored.
    result = StandardResult()

    try:
        if offline_preset == True:
            device_state = 'online'
        else:
            device_state = 'offline'

        method = "POST"
        path = f'v1/eventpreset/startupevent/{device_state}/{event_preset_id}'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        json_post_data = {
            "deviceID": device_id,
            "deviceGroupID": device_group_id
        }

        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        result.code = -1
        result.description = "Exception in set_startup_preset. Line number " + str(line_number)

    return result

