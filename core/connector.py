from netmiko import ConnectHandler
from netmiko.ssh_autodetect import SSHDetect
from netmiko.exceptions import NetMikoAuthenticationException, NetMikoTimeoutException
import subprocess
import platform


class HybridNetworkDevice:
    def __init__(self, hostname_or_ip, username, password):
        self.hostname = hostname_or_ip
        self.ip = hostname_or_ip
        self.username = username
        self.password = password
        self.device_os = None
        self.netmiko_conn = None

        self.detect_os_and_initialize()

    def detect_os_and_initialize(self):
        print(f"[~] Running SSHDetect for {self.hostname}")
        try:
            guesser = SSHDetect(
                device_type='autodetect',
                host=self.ip,
                username=self.username,
                password=self.password
            )
            self.device_os = guesser.autodetect()

            if not self.device_os:
                raise Exception("SSHDetect failed to determine device type")

            print(f"[+] Netmiko detected OS: {self.device_os}")

        except Exception as e:
            print(f"[-] SSHDetect failed: {e}")
            self.device_os = "unknown"

    def connect_netmiko(self):
        if self.netmiko_conn:
            return

        try:
            self.netmiko_conn = ConnectHandler(
                device_type=self.device_os or 'cisco_ios',
                ip=self.ip,
                username=self.username,
                password=self.password
            )
            print("[+] Netmiko connected")
        except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
            print(f"[-] Netmiko connection failed: {e}")
            self.netmiko_conn = None

    def run_command(self, command):
        if not self.netmiko_conn:
            self.connect_netmiko()
        if self.netmiko_conn:
            return self.netmiko_conn.send_command(command)
        else:
            print("[-] Netmiko not connected.")
            return None

    def disconnect(self):
        if self.netmiko_conn:
            try:
                self.netmiko_conn.disconnect()
            except Exception:
                pass

    def get_OS(self):
        return self.device_os


class HybridNetworkDeviceBuilder:
    def __init__(self, hostname_or_ip):
        self.hostname_or_ip = hostname_or_ip
        self.username = None
        self.password = None
        self.validate = False

    def with_credentials(self, username, password):
        self.username = username
        self.password = password
        return self

    def with_validation(self, validate):
        self.validate = validate
        return self

    def _ping_host(self):
        """Ping the host to validate reachability"""
        # Determine the appropriate ping command based on the OS
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', self.hostname_or_ip]
        
        try:
            # Run ping command and capture output
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5  # 5 second timeout
            )
            
            # Check if ping was successful
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"[-] Ping timeout for {self.hostname_or_ip}")
            return False
        except Exception as e:
            print(f"[-] Ping failed for {self.hostname_or_ip}: {e}")
            return False

    def build(self):
        if not self.username or not self.password:
            raise ValueError("Username and password must be set before building the device")
        
        if self.validate:
            print(f"[~] Validating reachability for {self.hostname_or_ip}")
            if not self._ping_host():
                raise ValueError(f"Failed to ping {self.hostname_or_ip}")
            print(f"[+] Host {self.hostname_or_ip} is reachable")
            
        device = HybridNetworkDevice(
            hostname_or_ip=self.hostname_or_ip,
            username=self.username,
            password=self.password
        )
            
        return device
