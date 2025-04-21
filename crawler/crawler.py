import threading
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime
from core.device_handler import DeviceHandler
from .fsm import DeviceState, DeviceFSM, StateTransition
from .data import Database

class Crawler:
    def __init__(self, db_path: str = "network_crawl.db", max_retries: int = 3, username: str = None, password: str = None):
        self.db = Database(db_path)
        self.max_retries = max_retries
        self.username = username
        self.password = password
        self._stop_event = threading.Event()
        self._workers: Dict[str, threading.Thread] = {}
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        if not self.username or not self.password:
            raise ValueError("Username and password must be provided")

    def add_seed_device(self, hostname: str, ip: str, username: str, password: str) -> None:
        """Add a seed device to start the crawl from."""
        device_id = self.db.add_device(hostname, ip)
        if device_id:
            self.logger.info(f"Added seed device {hostname} ({ip}) to queue")
        else:
            self.logger.warning(f"Device {hostname} ({ip}) already exists in database")

    def start(self, num_workers: int = 4) -> None:
        """Start the crawler with the specified number of worker threads."""
        self._stop_event.clear()
        for i in range(num_workers):
            worker_id = f"worker-{i}"
            worker = threading.Thread(
                target=self._worker_loop,
                args=(worker_id,),
                daemon=True
            )
            self._workers[worker_id] = worker
            worker.start()
            self.logger.info(f"Started worker {worker_id}")

    def stop(self) -> None:
        """Stop all worker threads gracefully."""
        self._stop_event.set()
        for worker_id, worker in self._workers.items():
            worker.join()
            self.logger.info(f"Stopped worker {worker_id}")

    def _worker_loop(self, worker_id: str) -> None:
        """Main worker loop that processes devices from the queue."""
        while not self._stop_event.is_set():
            try:
                device = self.db.get_next_queued_device(worker_id)
                if not device:
                    time.sleep(1)  # No work to do, wait a bit
                    continue

                self._process_device(device, worker_id)
            except Exception as e:
                self.logger.error(f"Worker {worker_id} encountered error: {str(e)}")
                time.sleep(5)  # Back off on error

    def _process_device(self, device: Dict[str, Any], worker_id: str) -> None:
        """Process a single device through the FSM states."""
        device_id = device['id']
        current_state = DeviceState[device['state']]
        
        try:
            if current_state == DeviceState.CONNECTING:
                self._handle_connecting(device, worker_id)
            elif current_state == DeviceState.COLLECTING:
                self._handle_collecting(device, worker_id)
            elif current_state == DeviceState.DISCOVERED:
                self._handle_discovered(device, worker_id)
            elif current_state == DeviceState.ENRICHED:
                self._handle_enriched(device, worker_id)
            elif current_state == DeviceState.ERROR:
                self._handle_error(device, worker_id)
        except Exception as e:
            self.logger.error(f"Error processing device {device['hostname']}: {str(e)}")
            transition = DeviceFSM.create_transition(
                current_state,
                DeviceState.ERROR,
                str(e)
            )
            self.db.update_device_state(device_id, transition)
            self.db.increment_retry_count(device_id)
        finally:
            self.db.release_device(device_id)

    def _handle_connecting(self, device: Dict[str, Any], worker_id: str) -> None:
        """Handle the connecting state."""
        device_id = device['id']
        handler = DeviceHandler(device['ip'], self.username, self.password)
        
        try:
            # Test connection
            handler.run("show version")
            
            transition = DeviceFSM.create_transition(
                DeviceState.CONNECTING,
                DeviceState.COLLECTING
            )
            self.db.update_device_state(device_id, transition)
        except Exception as e:
            transition = DeviceFSM.create_transition(
                DeviceState.CONNECTING,
                DeviceState.ERROR,
                str(e)
            )
            self.db.update_device_state(device_id, transition)
            raise

    def _handle_collecting(self, device: Dict[str, Any], worker_id: str) -> None:
        """Handle the collecting state."""
        device_id = device['id']
        handler = DeviceHandler(device['ip'], self.username, self.password)
        
        try:
            # Collect device information
            version_info = handler.get_version_info()
            inventory = handler.get_inventory()
            
            device_info = {
                'hostname': version_info.get('hostname'),
                'platform': version_info.get('platform'),
                'serial': inventory.get('serial') if inventory else None
            }
            
            self.db.update_device_info(device_id, device_info)
            
            transition = DeviceFSM.create_transition(
                DeviceState.COLLECTING,
                DeviceState.DISCOVERED
            )
            self.db.update_device_state(device_id, transition)
        except Exception as e:
            transition = DeviceFSM.create_transition(
                DeviceState.COLLECTING,
                DeviceState.ERROR,
                str(e)
            )
            self.db.update_device_state(device_id, transition)
            raise

    def _handle_discovered(self, device: Dict[str, Any], worker_id: str) -> None:
        """Handle the discovered state."""
        device_id = device['id']
        handler = DeviceHandler(device['ip'], self.username, self.password)
        
        try:
            # Get neighbors
            neighbors = handler.get_cdp_neighbors() or handler.get_lldp_neighbors()
            
            # Add neighbors to queue
            for neighbor in neighbors:
                self.db.add_device(
                    neighbor.get('hostname', 'unknown'),
                    neighbor.get('ip', 'unknown')
                )
            
            # Move to next state
            next_state = DeviceState.ENRICHED if not device['enriched'] else DeviceState.DONE
            transition = DeviceFSM.create_transition(
                DeviceState.DISCOVERED,
                next_state
            )
            self.db.update_device_state(device_id, transition)
        except Exception as e:
            transition = DeviceFSM.create_transition(
                DeviceState.DISCOVERED,
                DeviceState.ERROR,
                str(e)
            )
            self.db.update_device_state(device_id, transition)
            raise

    def _handle_enriched(self, device: Dict[str, Any], worker_id: str) -> None:
        """Handle the enriched state."""
        device_id = device['id']
        transition = DeviceFSM.create_transition(
            DeviceState.ENRICHED,
            DeviceState.DONE
        )
        self.db.update_device_state(device_id, transition)

    def _handle_error(self, device: Dict[str, Any], worker_id: str) -> None:
        """Handle the error state."""
        device_id = device['id']
        retry_count = self.db.get_device_retry_count(device_id)
        
        if retry_count < self.max_retries:
            transition = DeviceFSM.create_transition(
                DeviceState.ERROR,
                DeviceState.QUEUED
            )
            self.db.update_device_state(device_id, transition)
        else:
            self.logger.error(f"Device {device['hostname']} exceeded max retries")

