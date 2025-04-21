### test script for the network device class to grab cdp neighbors and print out the object info

from connect import NetworkDevice

device = NetworkDevice("cisco_ios", "192.168.1.1", "admin", "password")
print(device.get_facts())
print(device.get_cdp_neighbors())
device.disconnect()