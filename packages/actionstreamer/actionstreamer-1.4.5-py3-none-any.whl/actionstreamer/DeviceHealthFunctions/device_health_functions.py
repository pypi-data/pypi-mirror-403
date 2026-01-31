import math
import re
import time
import os
import psutil
import subprocess
import json
import platform
from typing import Any
from importlib.metadata import version
from actionstreamer.CommonFunctions import get_exception_info
from actionstreamer import Config
from actionstreamer.CommonFunctions import Wifi


def is_raspberry_pi():
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().lower()
            return 'raspberry pi' in model
    except FileNotFoundError:
        return False


# External requirements 

if platform.system().lower() == "linux":
    try:
        import ifaddr  # pyright: ignore

        if is_raspberry_pi():
            import smbus2  # pyright: ignore

    except ImportError:
        pass
else:
    # print("Skipping Linux-only imports.")
    pass


from actionstreamer import CommonFunctions


def get_link_quality(interface: str):

    try:
        # Run the iwconfig command and get the output
        result = subprocess.run(['iwconfig', interface], capture_output=True, text=True)
        output = result.stdout.strip()
        
        # Parse the output to find the link quality
        for line in output.split('\n'):
            if "Link Quality" in line:
                link_quality = line.split('=')[1].split()[0].strip()
                return link_quality
        return "Link quality not found"
    
    except Exception as e:
        return f"Error: {e}"


# Get info functions
def sum_list_of_numbers(number_list: list[int]) -> int:
    total: float = 0
    try:
        for number in number_list:
            total += number
    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in sum_list_of_numbers")
        return -1
    return total


def get_battery_voltage(system_management_bus: Any) -> float:
    raw_val: int = -1
    V1_BATTERY_SENSOR_ADDRESS = 0x36

    try:
        high_val: int = system_management_bus.read_byte_data(V1_BATTERY_SENSOR_ADDRESS, 0x02)
        low_val: int = system_management_bus.read_byte_data(V1_BATTERY_SENSOR_ADDRESS, 0x03)
        raw_val = ((low_val | (high_val << 8)) >> 4)
    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_battery_voltage")

    return raw_val * 1.25


def get_battery_percentage(system_management_bus: Any) -> float:

    battery_percent = -1
    V1_BATTERY_SENSOR_ADDRESS = 0x36

    try:        
        battery_percent = system_management_bus.read_byte_data(V1_BATTERY_SENSOR_ADDRESS, 0x04)
    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_battery_voltage")

    return battery_percent


def get_voltage_change(battery_voltage_history_array: list[float]) -> list[int]:

    voltage_change_array: list[int] = []

    for intIndex in range(len(battery_voltage_history_array) - 1):

        intNextIndex = intIndex + 1

        if battery_voltage_history_array[intIndex] == battery_voltage_history_array[intNextIndex]:
            voltage_change_array.append(0)
        elif battery_voltage_history_array[intIndex] > battery_voltage_history_array[intNextIndex]:
            voltage_change_array.append(1)
        else:
            voltage_change_array.append(-1)

    return voltage_change_array


def get_charge_status(hex_value: int) -> str:
    
    charge_states = {
        0x00: "Not Charging",
        0x01: "Trickle Charge",
        0x02: "Pre-charge",
        0x03: "Fast Charge (Constant Current mode)",
        0x04: "Taper Charge (Constant Voltage mode)",
        0x05: "Reserved",
        0x06: "Top-off Timer Active Charging",
        0x07: "Charge Termination Done"
    }
    
    top_bits = (hex_value >> 5) & 0x07
    
    return charge_states.get(top_bits, "Unknown Status")


def get_battery_info_v2(system_management_bus: Any):

    charge_circuit_i2c_address = 0x6B
    register_voltage_msb = 0x3B
    register_voltage_lsb = 0x3C
    register_status = 0x1C
    # register_control = 0x0F

    try:
        # # Set initial I2C parameters
        # system_management_bus.write_byte_data(charge_circuit_i2c_address, 0x2E, 0xB0)

        # # Set register before reading status
        # system_management_bus.write_byte_data(charge_circuit_i2c_address, register_control, 0xA2)
        # time.sleep(1)
        # hex_status = system_management_bus.read_byte_data(charge_circuit_i2c_address, register_status)
        
        # # Set register before reading voltage
        # system_management_bus.write_byte_data(charge_circuit_i2c_address, register_control, 0x82)
        # time.sleep(1)
        
        # msb = system_management_bus.read_byte_data(charge_circuit_i2c_address, register_voltage_msb)
        # lsb = system_management_bus.read_byte_data(charge_circuit_i2c_address, register_voltage_lsb)
        # raw_millivolts = (msb << 8) | lsb
        
        # if hex_status == 0x00: # Not charging
        #     adjusted_millivolts = raw_millivolts
        # else:
        #     adjusted_millivolts = raw_millivolts - 200
        
        # # Reset register
        # system_management_bus.write_byte_data(charge_circuit_i2c_address, register_control, 0xA2)
        
        # binary_status = bin(status)[2:].zfill(8)  # Convert to binary string with leading zeros
        
        # return raw_voltage, adjusted_voltage, hex(status)

        # Reading charger status
        hex_status = system_management_bus.read_byte_data(charge_circuit_i2c_address, register_status)
        
        msb = system_management_bus.read_byte_data(charge_circuit_i2c_address, register_voltage_msb)
        lsb = system_management_bus.read_byte_data(charge_circuit_i2c_address, register_voltage_lsb)
        raw_millivolts = (msb << 8) | lsb
        
        charge_termination_done = False

        first_three_bits = (hex_status >> 5) & 0b111

        if first_three_bits == 0b111:
            charge_termination_done = True

        if hex_status == 0x00 or charge_termination_done: # Not charging
            adjusted_millivolts = raw_millivolts
        else:
            adjusted_millivolts = raw_millivolts - 200
        
        percentage = adjusted_millivolts / 4000
        status_string = get_charge_status(hex_status) 

        battery_info = {
            'percent': percentage,
            'mV': adjusted_millivolts,
            'status': status_string,
        }

        return battery_info
    
    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        #return -1, "Error reading I2C: " + e
        return dummy_battery()
    

def get_battery_info(system_management_bus: Any, battery_voltage_history_array: Any, battery_status: Any) -> Any:

    try:
        battery_remaining: float = get_battery_percentage(system_management_bus)
        battery_voltage: float = get_battery_voltage(system_management_bus)

        if battery_voltage / 1000 > 4.15:
            battery_remaining = 100
        elif battery_voltage / 1000 < 3.2:
            battery_remaining = 0
        else:
            battery_remaining = math.ceil(-337 + 105 * battery_voltage)

        battery_voltage_history_array.insert(0, battery_voltage)
        intLength = len(battery_voltage_history_array) - 1

        if intLength > 4:

            battery_voltage_history_array.pop()

            aryVoltageChange: list[int] = get_voltage_change(battery_voltage_history_array)
            voltage_change = sum_list_of_numbers(aryVoltageChange)

            if voltage_change == 0:
                if battery_remaining >= 93:
                    battery_status[0] = "charged"
                else:
                    battery_status[0] = battery_status[0]
            elif voltage_change < 0:
                battery_status[0] = "depleting"

            elif voltage_change > 0:
                battery_status[0] = "charging"

            # print("{0}%\t {1}mV\t {2}".format(battery_remaining, battery_voltage, battery_status))

            battery_info = {
                'percent': battery_remaining,
                'mV': battery_voltage,
                'status': battery_status[0]
            }

        else:
            return dummy_battery()

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_battery_info")
        return dummy_battery()

    return battery_info


def dummy_battery():

    battery_info = {
        'percent': 0,
        'mV': 0,
        'status': 'missing'
    }

    return battery_info


def get_cpu_temp():

    cpuTemp_val = -1

    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as objFile:
            cpuTemp_raw_val = float(objFile.readline().split()[0])
            cpuTemp_val = cpuTemp_raw_val / 1000
    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_cpu_temp")

    return cpuTemp_val


def get_gpu_temp():

    gpuTemp_val = -1

    try:
        gpuTemp_raw_val = subprocess.check_output(["/usr/bin/vcgencmd", "measure_temp"])
        #print(gpuTemp_raw_val.decode())
        gpuTemp_val_1 = gpuTemp_raw_val.decode().split("=", 1)
        gpuTemp_val_2 = gpuTemp_val_1[1].split("'", 1)
        gpuTemp_val = gpuTemp_val_2[0]

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_gpu_temp")

    return gpuTemp_val


def get_system_datetime():

    sys_datetime_val = -1

    try:
        sys_datetime_val = float(round(time.time() * 1000))
    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_system_datetime")
    
    return sys_datetime_val


def get_system_uptime():

    sys_uptime_val = -1

    try:
        with open('/proc/uptime', 'r') as objFile:
            sys_uptime_secs_val = float(objFile.readline().split()[0])
            sys_uptime_val = int(sys_uptime_secs_val * 1000)
    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_system_uptime")

    return sys_uptime_val


def get_time_info():

    time_info = {
        'datetime': -1,
        'uptime': -1
    }

    try:
        sysDatetime = get_system_datetime()
        sysUptime = get_system_uptime()

        time_info = {
            'datetime': sysDatetime,
            'uptime': sysUptime
        }

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_time_info")

    return time_info


def get_disk_info():

    disk_usage_info = {
        'device': "/dev/root",
        'mountpoint': "/",
        'total': -1,
        'used': -1,
        'free': -1,
        'percent': -1
    }
    
    try:

        disk_usage = psutil.disk_usage("/")

        disk_usage_info = {
            'device': "/dev/root",
            'mountpoint': "/",
            'total': float(disk_usage.total),
            'used': float(disk_usage.used),
            'free': float(disk_usage.free),
            'percent': float(disk_usage.percent)
        }
    
    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_disk_info")

    return disk_usage_info


def get_cpu_info():

    cpu_usage_info = {
        'temp': -1,
        'percent': -1,
        'count': -1,
        'freq': -1
    }

    try:
        intCPUCount = psutil.cpu_count()
        dblCPUPercent = psutil.cpu_percent(interval=1, percpu=True)
        intCPUFrequency = psutil.cpu_freq()

        cpuTemp = get_cpu_temp()

        cpu_usage_info = {
            'temp': cpuTemp,
            'percent': dblCPUPercent,
            'count': intCPUCount,
            'freq': intCPUFrequency.current if intCPUFrequency else -1
        }

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_cpu_info")

    return cpu_usage_info


def get_gpu_info():

    gpu_usage_info = {
        'temp': -1
    }

    try:
        gpuTemp = get_gpu_temp()

        gpu_usage_info = {
            'temp': gpuTemp
        }

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_gpu_info")

    return gpu_usage_info


def get_memory_info():

    virtual_memory_usage_info = {
        'total': -1,
        'available': -1,
        'percent': -1,
        'used': -1,
        'free': -1,
        'active': -1,
        'inactive': -1,
        'buffers': -1,
        'cached': -1,
        'shared': -1
    }

    swap_memory_usage_info = {
        'total': -1,
        'used': -1,
        'free': -1,
        'percent': -1,
        'sin': -1,
        'sout': -1
    }

    memory_usage_info_obj = {
        'virtual_memory': virtual_memory_usage_info,
        'swap_memory': swap_memory_usage_info
    }
    
    try:
        try:
            memory_virtual_val = psutil.virtual_memory()

            virtual_memory_usage_info = {
                'total': memory_virtual_val.total,
                'available': memory_virtual_val.available,
                'percent': memory_virtual_val.percent,
                'used': memory_virtual_val.used,
                'free': memory_virtual_val.free,
                'active': memory_virtual_val.active,
                'inactive': memory_virtual_val.inactive,
                'buffers': memory_virtual_val.buffers,
                'cached': memory_virtual_val.cached,
                'shared': memory_virtual_val.shared
            }

        except:
            CommonFunctions.log_to_console("Error in get_memory_info. psutil.virtual_memory() failed")

        try:
            memory_swap_val = psutil.swap_memory()

            swap_memory_usage_info = {
                'total': memory_swap_val.total,
                'used': memory_swap_val.used,
                'free': memory_swap_val.free,
                'percent': memory_swap_val.percent,
                'sin': memory_swap_val.sin,
                'sout': memory_swap_val.sout
            }

        except:
            CommonFunctions.log_to_console("Error in get_memory_info. psutil.swap_memory() failed")

        memory_usage_info_obj = {
            'virtual_memory': virtual_memory_usage_info,
            'swap_memory': swap_memory_usage_info
        }

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_memory_info")

    return memory_usage_info_obj


def get_wireless_interface_info():

    wireless_interface_info = {
        'ap_mac_address': '-1',
        'ap_ssid': '-1',
        'freq': -1,
        'signal_dBm': -1,
        'tx_bitrate_mbps': -1,
        'mcs': -1
    }

    try:
        system = platform.system()

        if system == "Windows":
            # On Windows, most Wi-Fi info requires Location services or admin privileges
            # Safely return interface name, status, and speed using psutil
            net_stats = psutil.net_if_stats()

            wifi_keywords = ["wi-fi", "wifi", "wireless", "wlan"]

            for iface, stats in net_stats.items():
                iface_lower = iface.lower()
                if any(keyword in iface_lower for keyword in wifi_keywords):
                    wireless_interface_info['tx_bitrate_mbps'] = stats.speed if stats.speed > 0 else -1
                    break

        else:
            # Linux
            result = subprocess.run(["iw", "dev"], capture_output=True, text=True)
            adapter_name = ''
            if 'wlan1' in result.stdout:
                adapter_name = 'wlan1'
            elif 'wlan0' in result.stdout:
                adapter_name = 'wlan0'

            if adapter_name:
                wi_raw_value = subprocess.check_output(["iw", "dev", adapter_name, "link"])
                lines = [line.decode().strip() for line in wi_raw_value.splitlines()]

                ap_mac = ssid = freq = signal = tx_rate = mcs = -1

                for line in lines:
                    if line.startswith("Connected to"):
                        ap_mac = line.split()[2]
                    elif line.startswith("SSID:"):
                        ssid = line.split("SSID:")[1].strip()
                    elif line.startswith("freq:"):
                        freq = int(line.split()[1])
                    elif line.startswith("signal:"):
                        signal = int(line.split()[1])
                    elif line.startswith("tx bitrate:"):
                        parts = line.split()
                        tx_rate = float(parts[2])
                        if "MCS" in line:
                            mcs_index = parts.index("MCS")
                            mcs = int(parts[mcs_index + 1])

                wireless_interface_info = {
                    'ap_mac_address': ap_mac,
                    'ap_ssid': ssid,
                    'freq': freq,
                    'signal_dBm': signal,
                    'tx_bitrate_mbps': tx_rate,
                    'mcs': mcs
                }

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_wireless_interface_info")

    return wireless_interface_info


def get_iwconfig_info(environment: str):

    iwconfig_info = {
        'protocol': '-1',
        'tx_power_dBm': -1,
        'retry_short_limit': 0,
        'rts': 0,
        'frag': 0,
        'link_quality': '0/70',
        'rx_invalid_nwid': '-1',
        'rx_invalid_crypt': 0,
        'rx_invalid_frag': 0,
        'tx_excessive_retries': 0,
        'invalid_misc': 0,
        'missed_beacon': 0
    }

    try:
        result = subprocess.run(['iwconfig'], capture_output=True, text=True)

        if 'wlan1' in result.stdout:
            adapter_name = 'wlan1'
        elif 'wlan0' in result.stdout:
            adapter_name = 'wlan0'
        else:
            adapter_name = ''

        iwconfig_info_arr = []

        if adapter_name != '':

            iwconfig_raw_val = subprocess.check_output(["iwconfig", adapter_name])

            for iwconfig_raw_val_line in iwconfig_raw_val.decode().splitlines():
                iwconfig_list = [_f for _f in iwconfig_raw_val_line.split(" ") if _f]
                iwconfig_list_filtered = list([x.strip() for x in iwconfig_list])
                iwconfig_info_arr.append(iwconfig_list_filtered)

            # Parse TX Power
            try:
                tx_power_dBm = iwconfig_info_arr[2][3].strip("Tx-Power=")
            except:
                tx_power_dBm = 0
                pass

            # Parse retry_short_limit, rts, frag
            try:
                retry_short_limit = iwconfig_info_arr[3][2].strip("limit:")
            except:
                retry_short_limit = 0
                pass

            try:
                rts_i = iwconfig_info_arr[3].index("RTS")
                rts_i_loc = rts_i + 1
            except:
                rts_i = 0
                rts_i_loc = 1
                pass

            try:
                rts = iwconfig_info_arr[3][rts_i_loc].strip("thr").strip(":").strip("=")
            except:
                rts = 0
                pass

            try:
                frag_i = iwconfig_info_arr[3].index("Fragment")
                frag_i_loc = frag_i + 1
            except:
                pass

            try:
                frag = iwconfig_info_arr[3][frag_i_loc].strip("thr").strip(":").strip("=")
            except:
                frag = 0
                pass

            # Parse Link Quality
            if (environment != 'Standalone'):

                try:                
                    # link_quality = iwconfig_info_arr[5][1].strip("Quality=")
                    link_quality = get_link_quality(adapter_name)
                except:
                    link_quality = 0
                    pass
            
            # Parse RX
            try:
                rx_invalid_nwid = iwconfig_info_arr[6][2].strip("nwid:")
            except:
                rx_invalid_nwid = 0
                pass
            try:
                rx_invalid_crypt = iwconfig_info_arr[6][5].strip("crypt:")
            except:
                rx_invalid_crypt = 0
                pass
            try:
                rx_invalid_frag = iwconfig_info_arr[6][8].strip("frag:")
            except:
                rx_invalid_frag = 0
                pass

            # Parse TX
            try:
                tx_excessive_retries = iwconfig_info_arr[7][2].strip("retries:")
            except:
                tx_excessive_retries = 0
                pass
            try:
                invalid_misc = iwconfig_info_arr[7][4].strip("misc:")
            except:
                invalid_misc = 0
                pass
            try:
                missed_beacon = iwconfig_info_arr[7][6].strip("beacon:")
            except:
                missed_beacon = 0
                pass
            
            iwconfig_info = {
                'protocol': iwconfig_info_arr[0][2],
                'tx_power_dBm': tx_power_dBm,
                'retry_short_limit': retry_short_limit,
                'rts': rts,
                'frag': frag,
                'link_quality': link_quality,
                'rx_invalid_nwid': rx_invalid_nwid,
                'rx_invalid_crypt': rx_invalid_crypt,
                'rx_invalid_frag': rx_invalid_frag,
                'tx_excessive_retries': tx_excessive_retries,
                'invalid_misc': invalid_misc,
                'missed_beacon': missed_beacon
            }

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_iwconfig_info")

    return iwconfig_info


def get_ifconfig_info():

    rx_obj = {
        'bytes': -1,
        'packets': -1,
        'errors': -1,
        'dropped': -1,
        'overruns': -1,
        'frame': -1
    }

    tx_obj = {
        'bytes': -1,
        'packets': -1,
        'errors': -1,
        'dropped': -1,
        'overruns': -1,
        'carrier': '-1'
    }

    ifconfig_info = {
        'HWaddr':'-1',
        'mtu': -1,
        'metric': '0',
        'collisions': -1,
        'rx': rx_obj,
        'tx': tx_obj
    }

    try:

        wlan1_file_path = "/sys/class/net/wlan1/address"
        wlan0_file_path = "/sys/class/net/wlan0/address"

        if os.path.exists(wlan1_file_path):
            device_mac_address = subprocess.check_output(["cat", wlan1_file_path])

            try:
                device_mac_address = device_mac_address.rstrip()
            except:
                pass

        elif os.path.exists(wlan0_file_path):
            device_mac_address = subprocess.check_output(["cat", wlan0_file_path])

            try:
                device_mac_address = device_mac_address.rstrip()
            except:
                pass
        else:
            device_mac_address = "-1"

        ifconfig_info_arr = []

        result = subprocess.run(['iwconfig'], capture_output=True, text=True)

        if 'wlan1' in result.stdout:
            adapter_name = 'wlan1'
        elif 'wlan0' in result.stdout:
            adapter_name = 'wlan0'
        else:
            adapter_name = ''

        if adapter_name != '':

            ifconfig_raw_val = subprocess.check_output(["ifconfig", adapter_name])

            for ifconfig_raw_val_line in ifconfig_raw_val.splitlines():
                ifconfig_list = [_f for _f in ifconfig_raw_val_line.decode().split(" ") if _f]
                ifconfig_list_filtered = list([x.strip() for x in ifconfig_list])
                ifconfig_info_arr.append(ifconfig_list_filtered)


            # Parse RX
            try: 
                try:
                    rx_packets = ifconfig_info_arr[5][2]
                except:
                    pass
                try:
                    rx_errors = ifconfig_info_arr[6][2]
                except:
                    pass
                try:
                    rx_dropped = ifconfig_info_arr[6][4]
                except:
                    pass
                try:
                    rx_overruns = ifconfig_info_arr[6][6]
                except:
                    pass
                try:
                    rx_frame = ifconfig_info_arr[6][8]
                except:
                    rx_frame = -1
                try:
                    rx_bytes = ifconfig_info_arr[5][4]
                except:
                    pass

                # Create RX Object
                rx_obj = {
                    'bytes': rx_bytes,
                    'packets': rx_packets,
                    'errors': rx_errors,
                    'dropped': rx_dropped,
                    'overruns': rx_overruns,
                    'frame': rx_frame
                }
                
            except:
                filename, line_number = get_exception_info()
                if filename is not None and line_number is not None:
                    print(f"Exception occurred at line {line_number} in {filename}")
                CommonFunctions.log_to_console("Error in get_ifconfig_info. Parse RX failed")

            # Parse TX
            try: 
                try:
                    tx_packets = ifconfig_info_arr[7][2]
                except:
                    pass
                try:            
                    tx_errors = ifconfig_info_arr[8][2]
                except:
                    pass
                try:
                    tx_dropped = ifconfig_info_arr[8][4]
                except:
                    pass
                try:
                    tx_overruns = ifconfig_info_arr[8][6]
                except:
                    pass
                try:
                    tx_carrier = ifconfig_info_arr[8][8]
                except:
                    pass
                try:
                    tx_bytes = ifconfig_info_arr[7][4]
                except:
                    pass

                # Create TX Object
                tx_obj = {
                    'bytes': tx_bytes,
                    'packets': tx_packets,
                    'errors': tx_errors,
                    'dropped': tx_dropped,
                    'overruns': tx_overruns,
                    'carrier': tx_carrier
                }
                
            except:
                filename, line_number = get_exception_info()
                if filename is not None and line_number is not None:
                    print(f"Exception occurred at line {line_number} in {filename}")
                CommonFunctions.log_to_console("Error in get_ifconfig_info. Parse TX failed")

        # Parse MTU
        try:
            mtu = ifconfig_info_arr[0][3]
        except:
            #pass
            mtu = -1
            CommonFunctions.log_to_console("Error in get_ifconfig_info. Parse MTU failed")

        # Parse collisions & txqueuelen
        try:
            collisions = ifconfig_info_arr[8][10]
        except:
            # pass
            collisions = -1
            filename, line_number = get_exception_info()
            if filename is not None and line_number is not None:
                print(f"Exception occurred at line {line_number} in {filename}")
            CommonFunctions.log_to_console("Error in get_ifconfig_info. Parse collisions failed")
            
        # try:
        #     txqueuelen = ifconfig_info_arr[6][1].strip("txqueuelen:")
        # except:
            # pass

        # Parse HWaddr
        try:
            hw_address = device_mac_address.decode()
        except:
            hw_address = '-1'
            #CommonFunctions.log_to_console("Error in get_ifconfig_info. Parse HWaddr failed")

        metric = "0" # ifconfig_info_arr[3][5].strip("Metric:")

        ifconfig_info = {
            'HWaddr': hw_address,
            'mtu': mtu,
            'metric': metric,
            'collisions': collisions,
            'rx': rx_obj,
            'tx': tx_obj
        }

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_ifconfig_info")

    return ifconfig_info


def get_ip_address_array():

    interfaces_info = []

    try:
        interfaces = ifaddr.get_adapters()

        for iface in interfaces:
            for ip in iface.ips:
                if isinstance(ip.ip, tuple):
                    # IPv6 case
                    ip_address = ip.ip[0]
                else:
                    # IPv4 case
                    ip_address = ip.ip

                ip_info = {
                    'name': iface.nice_name,
                    'family': 'IPv6' if isinstance(ip.ip, tuple) else 'IPv4',
                    'ip': ip_address,
                    'netmask': ip.network_prefix,
                }

                interfaces_info.append(ip_info)
    
    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_ip_address_array")
    
    return interfaces_info


def get_radio_info(environment: str = 'Prod'):
     
    wiInfo = {}
    iwconfigInfo = {}
    ifconfigInfo = {}

    radio_info = {
        'wi': wiInfo,
        'iwconfig': iwconfigInfo,
        'ifconfig': ifconfigInfo
    }

    if (environment == 'Standalone'):
        return radio_info

    try:
        try:
            wiInfo = get_wireless_interface_info()        
        except:
            CommonFunctions.log_to_console("Error in get_radio_info. get_wireless_interface_info() failed")

        try:            
            iwconfigInfo = get_iwconfig_info(environment)        
        except:
            CommonFunctions.log_to_console("Error in get_radio_info. get_iwconfig_info() failed")

        try:            
            ifconfigInfo = get_ifconfig_info()        
        except:
            CommonFunctions.log_to_console("Error in get_radio_info. get_ifconfig_info() failed")

        radio_info = {
            'wi': wiInfo,
            'iwconfig': iwconfigInfo,
            'ifconfig': ifconfigInfo
        }

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_radio_info")

    return radio_info


def get_cpu_serial_number_linux() -> str:

    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.strip().startswith("Serial"):
                    return line.strip().split(":")[1].strip()
                
    except Exception as ex:
        return str(ex)


def get_camera_activity() -> str:

    try:
        camera_activity = ''
        separator = ''

        # Check if 'camera_multiplex.py' is running
        multiplex = subprocess.run('ps aux | grep camera_multiplex.py | grep -v grep', stdout=subprocess.PIPE, text=True, shell=True)

        if multiplex.stdout.strip():  # If there is any output
            camera_activity = camera_activity + separator + "Multiplex"
            separator = ', '

        # Check if 'record_video.py' is running
        record_video = subprocess.run('ps aux | grep record_video.py | grep -v grep', stdout=subprocess.PIPE, text=True, shell=True)

        if record_video.stdout.strip():  # If there is any output
            camera_activity = camera_activity + separator + "Recording"
            separator = ', '

        # Check if 'go_rtmp.sh' or 'go_rtmp_multiplex.sh' is running
        go_rtmp = subprocess.run('ps aux | grep go_rtmp | grep -v grep', stdout=subprocess.PIPE, text=True, shell=True)
        
        if go_rtmp.stdout.strip():  # If there is any output
            camera_activity = camera_activity + separator + "RTMP"
            separator = ', '
        
        # Check if 'gst-meet' is running
        gst_meet = subprocess.run('ps aux | grep gst-meet | grep -v grep', stdout=subprocess.PIPE, text=True, shell=True)
        
        if gst_meet.stdout.strip():  # If there is any output
            camera_activity = camera_activity + separator + "Conference"
            separator = ', '
        
        # Check if 'send' is running
        gst_meet = subprocess.run('ps aux | grep .appdata/ActionStreamer/scripts/send | grep -v grep', stdout=subprocess.PIPE, text=True, shell=True)
        
        if gst_meet.stdout.strip():  # If there is any output
            camera_activity = camera_activity + separator + "Streaming"
            separator = ', '
        
        # Check if 'gst-meet' is running
        capture_frames = subprocess.run('ps aux | grep capture_frames.py | grep -v grep', stdout=subprocess.PIPE, text=True, shell=True)
        
        if capture_frames.stdout.strip():  # If there is any output
            camera_activity = camera_activity + separator + "Capture frames"
            separator = ', '
        
        if camera_activity == '':
            camera_activity = 'Off'

        return camera_activity
    
    except Exception as ex:
        return f"Error: {ex}"


def get_throttling_status() -> str:

    try:
        # Run the 'vcgencmd get_throttled' command
        output = subprocess.check_output(['vcgencmd', 'get_throttled'], text=True)
        status = output.strip().split("=")[1]
        status_text = ''

        if status == "0x0":
            status_text = "No issues detected."
        elif int(status, 16) & 0x80000:
            status_text = "Under-voltage has occurred in the past."
        elif int(status, 16) & 0x50005:
            status_text = "Currently under-voltage and throttled."

        return status_text
        
    except Exception as e:
        #print(f"Error checking throttling status: {e}")
        return "Error"


def get_library_version(library_name):
    try:
        # Get the version of the specified library
        library_version = version(library_name)
        return library_version
    except Exception as e:
        # If there's an error (e.g., library not found), return the error message
        return f"Error getting version: {str(e)}"


def get_top_cpu_processes():
    os_username = CommonFunctions.get_login_user()
    cmd = (
        "ps -eo pid,%cpu,comm,args --sort=-%cpu --width=200 "
        "| grep -v '[p]s ' "
        f"| sed 's|/home/{os_username}/.appdata/ActionStreamer/||g' "
        "| head -6"  # Get the top 5 + header
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    lines = result.stdout.strip().split("\n")

    if not lines:
        return json.dumps({"top_processes": []}, indent=4)

    header = lines[0]  # Ensure the first row is a header
    data_lines = lines[1:]  # Exclude the header

    processes = []
    for line in data_lines:
        parts = line.split(maxsplit=3)  # Ensure args capture everything else
        if len(parts) < 3:
            continue  # Skip malformed lines

        pid, cpu_percent, command = parts[:3]
        args = parts[3] if len(parts) > 3 else ""

        process_info = {
            "pid": int(pid),
            "cpu_percent": float(cpu_percent),
            "command": command,
            "args": args
        }
        processes.append(process_info)

    return {"top_processes": processes}


def get_antenna() -> int:
    """
    Returns:
        1 if antenna 1 is in use (default),
        2 if antenna 2 is configured via dtparam=ant2,
       -1 if an error occurs.
    """
    config_file_path = '/boot/firmware/config.txt'

    try:
        with open(config_file_path, 'r') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                if 'dtparam=ant2' in stripped:
                    return 2
        return 1
    except Exception:
        return -1
    

def get_usb_capture_card() -> int:
    """
    Returns the card number of the USB microphone.
    If no USB microphone is found, returns -1.
    """
    try:
        output = subprocess.check_output(['arecord', '-l'], text=True)
        for line in output.splitlines():
            if "USB Audio Device" in line:
                # Extract the card number from the line
                match = re.search(r'card (\d+):', line)
                if match:
                    return int(match.group(1))
        return -1
    except Exception:
        return -1


def get_microphone_percent() -> int:
    """
    Returns the capture volume for the USB microphone as an integer percentage (0–100).
    Returns -1 if an error occurs or volume can't be determined.
    """
    card = get_usb_capture_card()
    if card == -1:
        return -1  # No USB microphone found

    try:
        output = subprocess.check_output(['amixer', '-c', str(card), 'get', 'Mic'], text=True)
        matches = re.findall(r'\[(\d{1,3})%\]', output)
        if matches:
            return int(matches[0])
        return -1
    except Exception:
        return -1


def get_usb_audio_output_percent() -> int:
    """
    Returns the playback/output volume (0–100) for the first USB audio card found.
    Returns -1 if no USB card or volume control is found.
    """
    try:
        # Find first USB playback card
        aplay_out = subprocess.check_output(['aplay', '-l'], text=True)
        card_match = re.search(r'card (\d+):.*usb', aplay_out, re.IGNORECASE)
        if not card_match:
            return -1
        card = card_match.group(1)

        # Query volume from common playback controls
        for control in ["Speaker", "Headphone", "PCM"]:
            try:
                amixer_out = subprocess.check_output(
                    ['amixer', '-c', card, 'get', control],
                    text=True
                )
                matches = re.findall(r'\[(\d{1,3})%\]', amixer_out)
                if matches:
                    return int(matches[0])
            except subprocess.CalledProcessError:
                continue  # Control not found, try next

        return -1
    
    except Exception:
        return -1


def get_device_config(config_folder_path):

    try:
        device_config = {
            'thumbnail_interval': float(Config.get_config_value(config_folder_path, 'ThumbnailInterval', '0')),
            'thumbnail_url': str(Config.get_config_value(config_folder_path, 'ThumbnailURL', '0')),
        }
    except:
        device_config = {
            'thumbnail_interval': 0,
            'thumbnail_url': '',
        }
        pass
    
    return device_config


def get_system_info(serial_number: str, system_management_bus: Any, v1_charger: bool = False, log_process_info: bool = False, environment: str = 'Prod', appdata_folder_path: str = '', config_folder_path: str = '', camera_status: str = ''):

    # Health variables/sys/class/net/wlan1/address    
    try:
        camera_activity = ''
        timeInfo = get_time_info()

        # Skip known exceptions to lower CPU usage.
        # To do: make this a check based on a device's capabilities rather than the environment.
        if (environment == "Standalone"):

            battery_info = dummy_battery()

        else:

            try:
                if v1_charger:
                #with smbus2.SMBus(1) as bus:
                    #batteryInfo = get_battery_info_v2(bus)
                    battery_info = get_battery_info(system_management_bus)
                else:
                    battery_info = get_battery_info_v2(system_management_bus)

            except Exception as ex:
                CommonFunctions.log_to_console(ex)
                battery_info = dummy_battery()

        try:
            software_date_file_path = os.path.join(appdata_folder_path, 'SoftwareUpdate.txt')
            software_date_file = open(software_date_file_path)
            software_date = software_date_file.readline()
            software_date_file.close()
        except:
            software_date = "No recent updates"
        
        try:
            software_version_file_path = os.path.join(appdata_folder_path, 'SoftwareVersion.txt')
            software_version_file = open(software_version_file_path)
            software_version = software_version_file.readline()
            software_version_file.close()
        except:
            software_version = "No recent updates"

        ip_address_info = get_ip_address_array()
        cpu_info = get_cpu_info()
        gpu_info = get_gpu_info()
        memory_info = get_memory_info()
        disk_info = get_disk_info()
        radio_info = get_radio_info(environment)
        camera_activity = get_camera_activity()
        throttle_status = get_throttling_status()

        if (environment == 'Standalone'):
            network_names = {}
            antenna_number = 0
        else:
            network_names = Wifi.get_network_names()
            antenna_number = get_antenna()
        
        microphone_percent = get_microphone_percent()
        audio_out_percent = get_usb_audio_output_percent()
        device_config = get_device_config(config_folder_path)
        last_clip_date = ''

        last_clip_date_file_path = os.path.join(appdata_folder_path, 'LastVideoClipDate.txt')

        try:
            if (os.path.exists(last_clip_date_file_path)):

                with open(last_clip_date_file_path, "r", encoding="utf-8") as last_clip_text_io_wrapper:
                    last_clip_date = last_clip_text_io_wrapper.read().strip()
        except:
            pass

        process_info = {}

        if log_process_info:
            process_info = get_top_cpu_processes()

        system_info = {
            'ip_addresses': ip_address_info,
            'time': timeInfo,
            'battery': battery_info,
            'cpu': cpu_info,
            'gpu': gpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'radio': radio_info,
            'camera': camera_status,
            'camera_activity': camera_activity,
            'last_clip_date': last_clip_date,
            'software': software_date,
            'version': software_version.strip(),
            'library_version': get_library_version('actionstreamer'),
            'serial_number': serial_number,
            'voltage_throttle': throttle_status,
            'network_names': network_names,
            'process_info': process_info,
            'antenna': antenna_number,
            'microphone_percent': microphone_percent,
            'audio_out_percent': audio_out_percent,
            'device_config': device_config
        }

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        CommonFunctions.log_to_console("Error in get_system_info")

    return system_info