import json
from typing import Dict, List
from urllib.parse import quote

from actionstreamer.Model import VideoClip, CreateVideoClip, PatchOperation, Event
from actionstreamer.Result import StandardResult, VideoClipResult, VideoClipListResult, EventResult
from actionstreamer.Config import WebServiceConfig
from actionstreamer.CommonFunctions import send_signed_request, get_exception_info
from actionstreamer.WebService.Patch import add_patch_operation, generate_patch_json


def create_video_clip(ws_config: WebServiceConfig, device_serial: str, create_video_clip: CreateVideoClip) -> VideoClipResult:

    video_clip_result = VideoClipResult()

    try:
        device_serial = device_serial.replace(" ", "")
        device_serial = quote(device_serial)

        method = "POST"
        path: str = 'v1/videoclip/' + device_serial
        url: str = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = json.dumps(create_video_clip.to_dict())

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

        video_clip_result.code = result.code
        video_clip_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            video_clip_result.video_clip = VideoClip(**json_dict)

            video_clip_result.code = result.code
            video_clip_result.description = result.description

    except Exception as ex:        
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        video_clip_result.code = -1
        video_clip_result.description = "Exception in create_video_clip. Line number " + str(line_number)

    return video_clip_result


def delete_video_clip(ws_config: WebServiceConfig, video_clip_id: int) -> StandardResult:

    """
    Delete a video clip.  This also deletes the associated file in the cloud if it has been uploaded.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    video_clip_id (int): The FileID.
    
    Returns:
    response_code: The API HTTP response code.
    response_string: The API HTTP response body
    """

    result = StandardResult()

    try:
        method = "DELETE"
        path = f'v1/videoclip/{video_clip_id}'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = ''

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:        
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.code = -1
        result.description = "Exception in delete_video_clip"

    return result


def create_video_clip_list(ws_config: WebServiceConfig, device_serial: str, video_clip_list: List[VideoClip]) -> VideoClipListResult:

    video_clip_list_result = VideoClipListResult()

    try:
        # Clean and encode device_serial
        device_serial = device_serial.replace(" ", "")
        device_serial = quote(device_serial)

        method = "POST"
        path = 'v1/videoclip/createlist/' + device_serial
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        
        # Convert the list of CreateVideoClip objects to a list of dictionaries for JSON serialization
        clips_data = [clip.to_dict() for clip in video_clip_list]
        body = json.dumps(clips_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

        video_clip_list_result.code = result.code
        video_clip_list_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            video_clip_list_result.video_clip_list = [VideoClip(**item) for item in json_dict]

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        video_clip_list_result.code = -1
        video_clip_list_result.description = "Exception in CreateVideoClipList. Line number " + str(line_number)

    return video_clip_list_result


def update_file_id(ws_config: WebServiceConfig, video_clip_id: int, file_id: int) -> StandardResult:

    result = StandardResult()

    try:
        operation_list: list[PatchOperation] = []
        add_patch_operation(operation_list, "FileID", str(file_id))

        method = "PATCH"
        path = 'v1/videoclip/' + str(video_clip_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = generate_patch_json(operation_list)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:        
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.code = -1
        result.description = "Exception in update_file_id Line number " + str(line_number)

    return result


def get_video_clip(ws_config: WebServiceConfig, video_clip_id: int) -> VideoClipResult:

    video_clip_result = VideoClipResult()

    try:
        method = "GET"
        path = 'v1/videoclip/' + str(video_clip_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}

        result = send_signed_request(ws_config, method, url, path, headers, parameters)

        video_clip_result.code = result.code
        video_clip_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            video_clip_result.video_clip = VideoClip(**json_dict)

    except Exception as ex:        
        video_clip_result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_video_clip at line {line_number} in {filename}")
        print(ex)
        video_clip_result.description = str(ex)

    return video_clip_result


def update_status(ws_config: WebServiceConfig, video_clip_id: int, status: int) -> StandardResult:

    result = StandardResult()

    try:
        operation_list: list[PatchOperation] = []
        add_patch_operation(operation_list, "VideoClipStatus", str(status))

        method = "PATCH"
        path = 'v1/videoclip/' + str(video_clip_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        body = generate_patch_json(operation_list)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:        
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        result.code = -1
        result.description = "Exception in VideoClip.update_status, line number " + str(line_number)

    return result


def get_video_clip_list(ws_config: WebServiceConfig, device_id: int, start_epoch: int, end_epoch: int, count: int = 0, order: str = 'desc', video_clip_type_id: int = 1, tags: list[int] = []) -> VideoClipListResult:

    video_clip_list_result = VideoClipListResult()

    try:

        method = "POST"
        path = 'v1/videoclip/list'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        
        json_post_data = {
            "deviceID": device_id,
            "startEpoch": start_epoch,
            "endEpoch": end_epoch,
            "count": count,
            "order": order,
            "videoClipTypeID": video_clip_type_id,
            "tagList": tags
        }

        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

        video_clip_list_result.code = result.code
        video_clip_list_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            video_clip_list_result.video_clip_list = [VideoClip(**item) for item in json_dict]

    except Exception as ex:        
        video_clip_list_result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_video_clip_list at line {line_number} in {filename}")
        print(ex)
        video_clip_list_result.description = str(ex)

    return video_clip_list_result


def get_extract_video_clip_list(ws_config: WebServiceConfig, serial_number: str, start_epoch: int, end_epoch: int) -> VideoClipListResult:

    video_clip_list_result = VideoClipListResult()

    try:
        method = "POST"
        path = 'v1/videoclip/extract/list'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters: dict[str, str] = {}
        
        json_post_data = {
            "deviceSerial": serial_number,
            "startEpoch": start_epoch,
            "endEpoch": end_epoch
        }

        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

        video_clip_list_result.code = result.code
        video_clip_list_result.description = result.description

        if result.code == 200:
            json_dict = json.loads(result.description)
            video_clip_list_result.video_clip_list = [VideoClip(**item) for item in json_dict]

    except Exception as ex:
        
        video_clip_list_result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_extract_video_clip_list at line {line_number} in {filename}")
        print(ex)
        video_clip_list_result.description = str(ex)

    return video_clip_list_result


def concatenate_clips(ws_config: WebServiceConfig, device_id: int, device_name: str, start_epoch: int, end_epoch: int, upload_url: str, postback_url: str, use_vrs: bool = False, timeout: int = 0) -> EventResult:

    # This endpoint enqueues an event for a device to make a longer clip from clips between two epoch times.
    # It returns the event object of the newly created event in order to let a user check the status.

    event_result = EventResult()

    try:

        method = "POST"
        path = 'v1/videoclip/concatenate'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}

        if use_vrs:
            status = 'True'
        else:
            status = 'False'

        query_params: Dict[str, str] = {
            "usevrs": status
        }

        json_post_data = {
            "deviceID": device_id,
            "deviceName": device_name,
            "startEpoch": start_epoch,
            "endEpoch": end_epoch,
            "uploadURL": upload_url,
            "postbackURL": postback_url,
            "timeout": timeout
        }

        body = json.dumps(json_post_data)

        result = send_signed_request(ws_config, method, url, path, headers, query_params, body)

        if result.code == 200:
            json_dict = json.loads(result.description)
            event_result.video_clip = Event(**json_dict)

            event_result.code = result.code
            event_result.description = result.description

    except Exception as ex:
        
        event_result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in concatenate_clips at line {line_number} in {filename}")
        print(ex)
        event_result.description = str(ex)

    return event_result