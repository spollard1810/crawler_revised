### test script for the network device class to grab cdp neighbors and print out the object info

from connector import HybridNetworkDeviceBuilder

device = (
    HybridNetworkDeviceBuilder("10.0.0.1")
    .with_credentials("admin", "hunter2")
    .build()
)


cdp = device.get_cdp_neighbors()
print(cdp)

device.disconnect()