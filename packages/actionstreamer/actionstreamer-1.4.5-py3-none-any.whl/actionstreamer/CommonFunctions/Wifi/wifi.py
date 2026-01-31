import json
import subprocess
from typing import TypedDict


class SavedNetwork(TypedDict):
    autoconnect: bool
    priority: int


class NetworkInfo(TypedDict):
    saved_networks: dict[str, SavedNetwork]
    network_count: int


def add_wifi_connection(ssid: str, password: str, connection_name: str, priority: int = 1) -> None:
    
    try:
        subprocess.run(['sudo', 'nmcli', 'connection', 'add', 'type', 'wifi', 'ifname', 'wlan0', 'con-name', connection_name, 'ssid', ssid, 'connection.autoconnect-priority', str(priority)], check=True)
        subprocess.run(['sudo', 'nmcli', 'connection', 'modify', connection_name, 'wifi-sec.key-mgmt', 'wpa-psk'], check=True)
        subprocess.run(['sudo', 'nmcli', 'connection', 'modify', connection_name, 'wifi-sec.psk', password], check=True)

        # Activate the connection
        try:
            subprocess.run(['sudo', 'nmcli', 'connection', 'up', connection_name], check=True)
            print(f"Added and activated new connection: {connection_name}")
        except:
            print(f"New connection added, but unable to connect: {connection_name}")
        
    except Exception as ex:
        print(f"Failed to add connection: {connection_name}. Error: {ex}")


def remove_wifi_connection(ssid: str) -> None:
    
    try:
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], check=True)
        print(f"Removed existing connection: {ssid}")
    except Exception:
        print(f"Failed to remove connection: {ssid}. It might not exist.")


def set_wifi_priority(ssid: str, priority: int) -> None:

    # Example usage:
    # set_wifi_priority("YourSSID", 100)

    try:
        # Get the UUID of the connection
        result = subprocess.run(
            ['nmcli', '-g', 'connection.uuid', 'connection', 'show', ssid],
            capture_output=True, text=True, check=True
        )
        uuid = result.stdout.strip()

        if not uuid:
            raise ValueError(f"Connection {ssid} not found.")

        # Set the autoconnect priority
        subprocess.run(
            ['nmcli', 'connection', 'modify', uuid, 'connection.autoconnect-priority', str(priority)],
            check=True
        )

        # Restart Network Manager to apply the changes
        subprocess.run(['sudo', 'systemctl', 'restart', 'NetworkManager'], check=True)

        print(f"Priority for {ssid} set to {priority}.")

    except Exception as ex:
        print(f"An error occurred while running nmcli: {ex}")


def back_up_connections(backup_file_path: str) -> None:
    # Backup all connection data to a JSON file
    try:
        result = subprocess.run(['sudo', 'nmcli', '--json', 'connection', 'export'], capture_output=True, text=True, check=True)
        connections_data = json.loads(result.stdout)
        
        with open(backup_file_path, 'w') as f:
            json.dump(connections_data, f, indent=4)
        
        print(f"Connections backed up to {backup_file_path}.")

    except Exception as ex:
        print(f"Failed to backup connections. Error: {ex}")


def restore_connections(backup_file_path: str) -> None:
    # Restore all connections from a JSON backup file
    try:
        with open(backup_file_path, 'r') as f:
            connections_data = json.load(f)

        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', 'id', 'all'], check=True)

        for connection in connections_data:
            subprocess.run(['sudo', 'nmcli', 'connection', 'import', 'json', json.dumps(connection)], check=True)
        
        print(f"Connections restored from {backup_file_path}.")

    except Exception as ex:
        print(f"Failed to restore connections. Error: {ex}")
        

def get_network_names() -> NetworkInfo:
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,AUTOCONNECT,AUTOCONNECT-PRIORITY,TYPE", "connection", "show"],
            capture_output=True, text=True, check=True
        )

        networks: dict[str, SavedNetwork] = {}

        for line in result.stdout.splitlines():
            if line:
                parts = line.split(":")
                if len(parts) > 3 and parts[3] == "802-11-wireless":
                    name = parts[0]
                    priority = int(parts[2]) if parts[2].isdigit() else 0
                    networks[name] = {"autoconnect": parts[1] == "yes", "priority": priority}

        return {"saved_networks": networks, "network_count": len(networks)}

    except Exception:
        return {"saved_networks": {}, "network_count": 0}