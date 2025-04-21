### Test script for the network device class

from connect import NetworkDevice

device = NetworkDevice("cisco_ios", "192.168.1.1", "admin", "password")

print(device.get_device_type())