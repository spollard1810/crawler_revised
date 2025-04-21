import paramiko
from netmiko import ConnectHandler

class NetworkDevice:
    def __init__(self, hostname, ip, username, password, device_type=None):
        self.hostname = hostname
        self.ip = ip
        self.username = username
        self.password = password
        self.connection = None
        self.device_type = device_type or self.get_device_type()

    def connect(self):
        self.connection = ConnectHandler(
            device_type=self.device_type,
            ip=self.ip,
            username=self.username,
            password=self.password
        )

    def run_command(self, command):
        if not self.connection:
            self.connect()
        return self.connection.send_command(command)

    def disconnect(self):
        if self.connection:
            self.connection.disconnect()

    def get_device_type(self):
        try:
            version_output = self.run_command("show version")
            
            # Cisco IOS
            if "Cisco IOS Software" in version_output:
                if "IOS-XE" in version_output:
                    return "cisco_xe"
                elif "IOS-XR" in version_output:
                    return "cisco_xr"
                elif "Nexus" in version_output:
                    return "cisco_nxos"
                else:
                    return "cisco_ios"
            
            # Cisco ASA
            elif "Cisco Adaptive Security Appliance" in version_output:
                return "cisco_asa"
            
            # Cisco WLC
            elif "Cisco Controller" in version_output:
                return "cisco_wlc"
            
            # Cisco ACI
            elif "Cisco Application Centric Infrastructure" in version_output:
                return "cisco_aci"
            
            # Cisco Meraki
            elif "Cisco Meraki" in version_output:
                return "cisco_meraki"
            
            # Arista
            elif "Arista" in version_output:
                return "arista_eos"
            
            # Default case
            else:
                return "unknown"
                
        except Exception as e:
            print(f"Error detecting device type: {str(e)}")
            return "unknown"