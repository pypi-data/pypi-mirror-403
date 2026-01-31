import json
import os
import platform
import shutil
from typing import Any, Dict, Optional, Mapping, cast
from actionstreamer import Model

class WebServiceConfig:
    
    """
    Configuration for connecting to the web service.

    Attributes:
        access_key (str): The access key for authentication.
        secret_key (str): The secret key for authentication.
        base_url (str): The base URL of the web service.
        timeout (int): The timeout for requests in seconds.
        ignore_ssl (bool): Whether to ignore SSL verification.
    """        
    def __init__(self, access_key: str, secret_key: str, base_url: str, timeout: int = 30, ignore_ssl: bool = False):
        """
        Initialize the WebServiceConfig. 
        The user is explicitly entrusted to called the from_config_folder if not providing any parameters

        :param access_key: The access key for authentication.
        :param secret_key: The secret key for authentication.
        :param base_url: The base URL of the web service.
        :param timeout: The timeout for requests in seconds (default is 30).
        :param ignore_ssl: Whether to ignore SSL verification (default is False).
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.timeout = timeout
        self.ignore_ssl = ignore_ssl

    @classmethod
    def from_config_folder(cls, config_folder_path: str, timeout: int = 30):
        # Get environment, default to Prod
        try:
            environment = get_config_value(config_folder_path, "Environment") or "Prod"
        except (FileNotFoundError, KeyError):
            environment = "Prod"

        # Set ignore_ssl based on environment
        ignore_ssl = environment.lower() != "prod"

        # Create instance
        return cls(
            access_key = get_config_value(config_folder_path, "AccessKey"),
            secret_key = get_config_value(config_folder_path, "SecretKey"),
            base_url = get_config_value(config_folder_path, f"WebServiceBaseUrl_{environment}"),
            timeout = timeout,
            ignore_ssl = ignore_ssl
        )


class LogConfig:

    def __init__(self, ws_config: WebServiceConfig, device_serial: str, agent_type: str, agent_version: str, agent_index: int, process_id: int, device_name: str = ''):
        self.ws_config = ws_config
        self.device_name = device_name
        self.device_serial = device_serial
        self.agent_type = agent_type
        self.agent_version = agent_version
        self.agent_index = agent_index
        self.process_id = process_id


class AppConfig:

    def __init__(self, os_username: str, device: Model.Device, config_folder_path: str, appdata_folder_path: str, environment: str, home_folder_path: str, ramdrive_folder_path: str, event_folder_path: str):
        self.os_username = os_username
        self.device = device
        self.config_folder_path = config_folder_path
        self.appdata_folder_path = appdata_folder_path
        self.environment = environment
        self.home_folder_path = home_folder_path
        self.ramdrive_folder_path = ramdrive_folder_path
        self.event_folder_path = event_folder_path


def is_windows() -> bool:
    return platform.system() == 'Windows'


def get_config_folder_path(app_name: str, base_folder_path: str = '') -> str:

    if is_windows():
        username = os.getlogin()
        config_dir = os.path.join('C:\\Users', username, 'AppData', 'Roaming', app_name, "config")
        # If a virtual environment is used, the path will be in something like:
        # C:\Users\Username\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\Roaming

    else:
        if base_folder_path:
            config_dir = os.path.join(base_folder_path, ".config", app_name)
        else:
            config_dir = os.path.expanduser(os.path.join("~", ".config", app_name))

    # Create the directory if it doesn't exist
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    return config_dir


def get_appdata_folder_path(app_name: str, base_folder_path: str = '') -> str:

    if is_windows():
        username = os.getlogin()
        appdata_folder_path = os.path.join('C:\\Users', username, 'AppData', 'Roaming', app_name)
        # If a virtual environment is used, the path will be in something like:
        # C:\Users\Username\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\Roaming
    else:
        if base_folder_path:
            appdata_folder_path = os.path.join(base_folder_path, ".appdata", app_name)
        else:
            appdata_folder_path = os.path.expanduser(os.path.join("~", ".appdata", app_name))

    # Create the directory if it doesn't exist
    if not os.path.exists(appdata_folder_path):
        os.makedirs(appdata_folder_path)

    return appdata_folder_path


def get_config_value(config_folder_path: str, name: str, default_value: str = '') -> str:

    if not os.path.exists(config_folder_path):
        os.makedirs(config_folder_path)

    file_path = os.path.join(config_folder_path, name + '.txt')
    
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            file.write(default_value)

    try:
        with open(file_path, 'r') as file:
            contents = file.read().strip()
        return contents
    except FileNotFoundError:
        print(f"File '{name}' not found in the specified folder '{config_folder_path}'")
        return ''
    except Exception as ex:
        print(f"Error occurred while reading '{name}': {ex}")
        return ''


def set_config_value(config_folder_path: str, name: str, value: str) -> bool:

    if not os.path.exists(config_folder_path):
        os.makedirs(config_folder_path)

    # Create the directory if it doesn't exist
    if not os.path.exists(config_folder_path):
        os.makedirs(config_folder_path)

    file_path = os.path.join(config_folder_path, name + '.txt')

    # Create backup folder and copy previous config value to it.
    backup_config_folder_path = os.path.join(config_folder_path, "backup")
    os.makedirs(backup_config_folder_path, exist_ok=True)  # Creates folder if missing

    backup_file_path = os.path.join(backup_config_folder_path, name + ".txt")
    shutil.copy(file_path, backup_file_path)

    try:
        with open(file_path, 'w') as file:
            file.write(value)
        print(f"Successfully set the value in '{name}'")

        return True
    
    except Exception as ex:
        print(f"Error occurred while setting value in '{name}': {ex}")
        return False


def reset_config_values(config_folder_path: str):
    """
    Resets the config values based on backups in {config_folder_path}/backup
    
    :config_folder_path: str = The folder path that holds the standard configs
    :return: A boolean indicating the file was reset
    """
    backup_folder_path = os.path.join(config_folder_path, "backup")

    # If backup folder doesn't exist, treat as "no action needed"
    if not os.path.isdir(backup_folder_path):
        return True
    
    # Loop over all files in the source folder
    try:
        for filename in os.listdir(backup_folder_path):

            source_file_path = os.path.join(backup_folder_path, filename)

            # Skip directories
            if not os.path.isfile(source_file_path):
                continue
            
            # Create destination file path
            destination_file_path = os.path.join(config_folder_path, filename)

            # Overwrite the destination file with the current source file
            shutil.copy(source_file_path, destination_file_path)

    except Exception as ex:
        print(f"Error occurred while resetting config values: {ex}")
        return False
    
    finally:
        # Delete the folder containing backup files 
        clear_backup_config_folder(backup_folder_path)

    return True


def clear_backup_config_folder(config_folder_path: str):
    """
    Clears the backup folder path by removing the files in the directory
    
    :param config_folder_path: folder path of config folder
    :type config_folder_path: str
    :return: boolean indicating success
    """
    backup_folder_path = os.path.join(config_folder_path, "backup")

    if not os.path.isdir(backup_folder_path):
        return True
    
    try:
        for entry in os.listdir(backup_folder_path):
            full_path = os.path.join(backup_folder_path, entry)

            if os.path.isfile(full_path) or os.path.islink(full_path):
                os.unlink(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)

    except Exception as ex:
        print(f"Error occurred while clearing backup config folder: {ex}")
        return False
    
    return True


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON from file."""
    with open(file_path, "r", encoding="utf-8") as file_handle:
        data: Dict[str, Any] = json.load(file_handle)
        return data


def save_json(file_path: str, data: Dict[str, Any]) -> None:
    """Save JSON to file, ensuring directories exist."""
    parent_folder_path = os.path.dirname(file_path)
    
    if parent_folder_path:
        os.makedirs(parent_folder_path, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file_handle:
        json.dump(data, file_handle, indent=4)


def get_json_value(data: dict[str, Any], path: str) -> Optional[Any]:
    keys = path.split(".")
    current_value: Any = data

    for key in keys:
        if not isinstance(current_value, Mapping) or key not in current_value:
            return None

        current_value = current_value[key]   # pyright: ignore[reportUnknownVariableType]

    return cast(Any, current_value)


def set_json_value(data: Dict[str, Any], path: str, value: Any) -> None:
    """Set a value in a nested dictionary using a dot-separated path."""
    keys = path.split(".")
    current_dict: Dict[str, Any] = data

    for key in keys[:-1]:
        if key not in current_dict or not isinstance(current_dict[key], dict):
            current_dict[key] = {}

        current_dict = current_dict[key]

    current_dict[keys[-1]] = value


def read_json_value(file_path: str, json_path: str) -> Optional[Any]:
    """Read a value from a JSON file using a path."""
    data = load_json(file_path)
    return get_json_value(data, json_path)


def write_json_value(file_path: str, json_path: str, value: Any) -> None:
    """Write a value to a JSON file using a path."""
    data = load_json(file_path)
    set_json_value(data, json_path, value)
    save_json(file_path, data)

# # Example usage
# config_path = "config.json"

# # Set a value
# write_value(config_path, "myroot.mychild.isenabled", True)

# # Get a value
# print(read_value(config_path, "myroot.mychild.isenabled"))  # Output: True
