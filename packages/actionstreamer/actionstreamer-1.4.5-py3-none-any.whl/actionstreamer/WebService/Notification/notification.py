import json

from actionstreamer.Config import WebServiceConfig
from actionstreamer.Model import Notification
from actionstreamer.Result import NotificationListResult, StandardResult
from actionstreamer.CommonFunctions import send_signed_request, get_exception_info


def get_notification_list(ws_config: WebServiceConfig, last_epoch_time: int, seen_in_app: bool = False, sent_as_email: bool = False) -> NotificationListResult:

    notification_list_result = NotificationListResult()
    result = StandardResult()
    
    try:
        method = "GET"
        path = 'v1/notification/list'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
                
        parameters = {
            "last_epoch_time": str(last_epoch_time),
            "seen_in_app": str(seen_in_app).lower(),
            "sent_as_email": str(sent_as_email).lower()
        }
        
        body = ''

        result = send_signed_request(ws_config, method, url, path, headers, parameters, body)

        if result.code == 200:
            json_dict = json.loads(result.description)
            notification_list_result.notification_list = [Notification(**item) for item in json_dict]

    except Exception as ex:   

        result.code = -1
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_notification_list at line {line_number} in {filename}")
        print(ex)
        result.description = str(ex)

    notification_list_result.code = result.code
    notification_list_result.description = result.description

    return notification_list_result