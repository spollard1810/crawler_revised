from core import DeviceHandler
from crawler import CrawlerBuilder

#test cases for core
#handler = DeviceHandler("192.168.1.1", "admin", "password")

#raw_output = handler.run("show interface")

#parsed_output = handler.run_and_parse("show interface")


# Initialize the builder
builder = CrawlerBuilder()

# Configure the crawler
builder.with_seed_device(
    hostname="router1.example.com",  # The hostname to start crawling from
    username="admin",                # SSH username
    password="password"              # SSH password
)

# Start the crawler
builder.start()