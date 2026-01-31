import json
from typing import Any, TypeAlias, Self

class DeviceHealthRow:

    extra_fields: dict[str, Any]

    def __init__(
        self,
        key: int = 0,
        device_name: str = '',
        serial_number: str = '',
        battery_status: str = '',
        battery_percent: float = 0.0,
        battery_voltage: float = 0.0,
        cpu_temp: float = 0.0,
        gpu_temp: float = 0.0,
        cpu_percent: str = '',
        access_point_name: str = '',
        network_alias: str = '',
        frequency: float = 0.0,
        link_quality: str = '',
        signal_strength_dbm: float = 0.0,
        transfer_bitrate_mbps: float = 0.0,
        device_status: str = '',
        camera_status: str = '',
        camera_activity: str = '',
        tunnel_status: str = '',
        software_version: str = '',
        last_heard_from_date: str = '',
        last_video_clip_date: str = '',
        software_deploy_date: str = '',
        **kwargs: Any
    ):
        self.key = key
        self.device_name = device_name
        self.serial_number = serial_number
        self.battery_status = battery_status
        self.battery_percent = battery_percent
        self.battery_voltage = battery_voltage
        self.cpu_temp = cpu_temp
        self.gpu_temp = gpu_temp
        self.cpu_percent = cpu_percent
        self.access_point_name = access_point_name
        self.network_alias = network_alias
        self.frequency = frequency
        self.link_quality = link_quality
        self.signal_strength_dbm = signal_strength_dbm
        self.transfer_bitrate_mbps = transfer_bitrate_mbps
        self.device_status = device_status
        self.camera_status = camera_status
        self.camera_activity = camera_activity
        self.tunnel_status = tunnel_status
        self.software_version = software_version
        self.last_heard_from_date = last_heard_from_date
        self.last_video_clip_date = last_video_clip_date
        self.software_deploy_date = software_deploy_date

        camel_to_snake = {
            "deviceName": "device_name",
            "serialNumber": "serial_number",
            "batteryStatus": "battery_status",
            "batteryPercent": "battery_percent",
            "batteryVoltage": "battery_voltage",
            "cpuTemp": "cpu_temp",
            "gpuTemp": "gpu_temp",
            "cpuPercent": "cpu_percent",
            "accessPointName": "access_point_name",
            "networkAlias": "network_alias",
            "frequency": "frequency",
            "linkQuality": "link_quality",
            "signalStrength_dBm": "signal_strength_dbm",
            "transferBitrate_Mbps": "transfer_bitrate_mbps",
            "deviceStatus": "device_status",
            "cameraStatus": "camera_status",
            "cameraActivity": "camera_activity",
            "tunnelStatus": "tunnel_status",
            "softwareVersion": "software_version",
            "lastHeardFromDate": "last_heard_from_date",
            "lastVideoClipDate": "last_video_clip_date",
            "softwareDeployDate": "software_deploy_date",
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "key": self.key,
            "deviceName": self.device_name,
            "serialNumber": self.serial_number,
            "batteryStatus": self.battery_status,
            "batteryPercent": self.battery_percent,
            "batteryVoltage": self.battery_voltage,
            "cpuTemp": self.cpu_temp,
            "gpuTemp": self.gpu_temp,
            "cpuPercent": self.cpu_percent,
            "accessPointName": self.access_point_name,
            "networkAlias": self.network_alias,
            "frequency": self.frequency,
            "linkQuality": self.link_quality,
            "signalStrength_dBm": self.signal_strength_dbm,
            "transferBitrate_Mbps": self.transfer_bitrate_mbps,
            "deviceStatus": self.device_status,
            "cameraStatus": self.camera_status,
            "cameraActivity": self.camera_activity,
            "tunnelStatus": self.tunnel_status,
            "softwareVersion": self.software_version,
            "lastHeardFromDate": self.last_heard_from_date,
            "lastVideoClipDate": self.last_video_clip_date,
            "softwareDeployDate": self.software_deploy_date,
        }

    def to_json(self):
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> Self:
        return cls(**mapping)


DeviceHealthRowList: TypeAlias = list[DeviceHealthRow]