import json

from actionstreamer.CommonFunctions import get_exception_info, send_signed_request
from actionstreamer.Config import WebServiceConfig
from actionstreamer.Result import StandardResult

def get_tags_for_uploaded_temp_image(ws_config: WebServiceConfig, object_name: str, device_id: int, device_serial: str, video_clip_id: int = 0, epoch_time: int = 0, epoch_time_ms: int = 0, max_labels:int = 4, min_confidence:float = 80) -> StandardResult:

    """
    Get tags for an image using AWS Recognition.
    The file must have already been uploaded using a signed URL for ActionStreamer's temporary cloud storage.
    If optional arguments are omitted, the web service will not add records to the database, it will simply return the tags.
    Return an array of {Label: str, Confidence: float}.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    object_name (string): The uploaded file's object name.
    device_id (int): The device that recorded the video where the image was extracted.
    device_serial (string): The device serial that recorded the video where the image was extracted.
    video_clip_id: The video clip the image was extracted from. Optional.
    epoch_time: The epoch timestamp of the frame. Optional.
    epoch_time_ms: The millisecond value of the timestamp. Optional.
    
    Returns:
    response_code: The API HTTP response code.
    response_string: The API HTTP response body
    """

    result = StandardResult()

    try:
        # Call the web service to get the tags for this image.
        json_post_data = {"objectName": object_name, "deviceID": device_id, "videoClipID": video_clip_id, "epochTime": epoch_time, "epochTimeMs": epoch_time_ms, "maxLabels": max_labels, "minConfidence": min_confidence}

        method = "POST"
        path = 'v1/tag/image/'+ str(device_serial)
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
        result.description = "Exception in get_tags_for_uploaded_temp_image"

    return result


def create_tags_for_video_clip(ws_config: WebServiceConfig, video_clip_id: str) -> StandardResult:

    """
    Inserts tags into the database for a video clip using AWS Recognition.
    The file must have already been uploaded to ActionStreamer's cloud storage.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    video_clip_id: The video clip ID.
    
    Returns:
    response_code: The API HTTP response code.
    response_string: The API HTTP response body
    """

    result = StandardResult()

    try:
        # Call the web service to create the tags for this image.
        json_post_data = {"videoClipID": video_clip_id}

        method = "POST"
        path = 'v1/tag/videoclip'
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
        result.description = "Exception in create_tags_for_video_clip"

    return result
