# Network Discovery Crawler

A Python-based network discovery framework that crawls networks using SSH, discovers neighbors via CDP/LLDP, and collects structured device metadata.

## Features

- Multi-threaded network device discovery
- CDP/LLDP neighbor discovery
- Device metadata collection
- Finite State Machine (FSM) for tracking crawl progress
- SQLite database for persistent storage
- Thread-safe operations
- Error handling and retry mechanisms

## Components

### Core Modules

- `crawler.py`: Main crawler implementation
  - Multi-threaded worker pool
  - Device processing logic
  - Error handling and retries

- `fsm.py`: Finite State Machine
  - Device state definitions
  - State transition validation
  - Transition history tracking

- `data.py`: Database Operations
  - SQLite schema management
  - Thread-safe database access
  - Device queue management

- `crawl.py`: Entry Point
  - Command-line interface
  - Configuration management
  - Process lifecycle control

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure SSH access to network devices with appropriate credentials

## Usage

### Basic Usage

```python
from crawler.crawler import Crawler

# Initialize crawler
crawler = Crawler(db_path="network_crawl.db")

# Add seed device
crawler.add_seed_device(
    hostname="router1",
    ip="192.168.1.1",
    username="admin",
    password="password"
)

# Start crawling with 4 worker threads
crawler.start(num_workers=4)
```

### Command Line Interface

```bash
python -m crawler.crawl \
    --seed-ip 192.168.1.1 \
    --seed-hostname router1 \
    --username admin \
    --password password \
    --workers 4 \
    --max-retries 3
```

## Device States

The crawler uses a Finite State Machine to track device progress:

1. `QUEUED`: Device waiting to be processed
2. `CONNECTING`: Establishing SSH connection
3. `COLLECTING`: Gathering device information
4. `DISCOVERED`: Neighbors found via CDP/LLDP
5. `ENRICHED`: Additional data collected
6. `DONE`: Processing complete
7. `ERROR`: Processing failed

## Database Schema

The SQLite database stores:

- Device information (hostname, IP, platform, etc.)
- State transitions
- Error messages
- Processing timestamps
- Retry counts

## Error Handling

- Automatic retry for failed devices (configurable max attempts)
- Error state tracking and logging
- Graceful handling of connection failures
- Timeout for stale connections

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here] 