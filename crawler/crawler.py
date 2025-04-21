import threading
import time
import logging
import uuid
from typing import Optional, Dict, Any, Tuple
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

from .data import Database
from .fsm import DeviceFSM, DeviceState
from core.device_handler import DeviceHandler

class CrawlerWorker:
    def __init__(self, worker_id: str, db: Database, fsm: DeviceFSM, credentials: Dict[str, str]):
        self.worker_id = worker_id
        self.db = db
        self.fsm = fsm
        self.credentials = credentials
        self.logger = logging.getLogger(f"worker-{worker_id}")

    def process_device(self, device: Dict[str, Any]):
        """Process a single device through the FSM states."""
        try:
            # Update state to connecting
            self.db.update_device_state(device['id'], DeviceState.CONNECTING.value)
            
            # Connect to device
            handler = DeviceHandler(
                device['ip'],
                self.credentials['username'],
                self.credentials['password']
            )
            try:
                # Update state to collecting
                self.db.update_device_state(device['id'], DeviceState.COLLECTING.value)
                
                # Collect device information
                version_info = handler.get_version_info()
                inventory = handler.get_inventory()
                
                # Update device info
                self.db.update_device_info(
                    device['id'],
                    hostname=version_info.get('hostname'),
                    platform=version_info.get('platform'),
                    serial=inventory.get('serial'),
                    last_seen=time.time()
                )
                
                # Discover neighbors
                neighbors = handler.get_cdp_neighbors() or handler.get_lldp_neighbors()
                if neighbors:
                    self.db.add_neighbors(device['id'], neighbors)
                    self.db.update_device_state(device['id'], DeviceState.DISCOVERED.value)
                    
                    # Add new neighbors to queue
                    for neighbor in neighbors:
                        if not self.db.get_device_by_ip(neighbor['ip']):
                            self.db.add_device(neighbor['ip'], neighbor['hostname'])
                else:
                    self.db.update_device_state(device['id'], DeviceState.DONE.value)
                
            except Exception as e:
                self.logger.error(f"Error processing device {device['ip']}: {str(e)}")
                self.db.update_device_state(
                    device['id'], 
                    DeviceState.ERROR.value,
                    error_msg=str(e)
                )
            finally:
                handler.disconnect()
                
        except Exception as e:
            self.logger.error(f"Critical error processing device {device['ip']}: {str(e)}")
            self.db.update_device_state(
                device['id'], 
                DeviceState.ERROR.value,
                error_msg=str(e)
            )

class NetworkCrawler:
    def __init__(self, db: Database, max_workers: int = 5, credentials: Optional[Dict[str, str]] = None, seed_ip: Optional[str] = None):
        self.db = db
        self.fsm = DeviceFSM()
        self.max_workers = max_workers
        self.credentials = credentials or {}
        self.seed_ip = seed_ip
        self.logger = logging.getLogger("crawler")
        self._stop_event = threading.Event()
        self._cleanup_thread = threading.Thread(target=self._cleanup_stale_claims, daemon=True)
        self._seed_processed = threading.Event()

    def _get_next_device(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get the next device to process, prioritizing the seed device."""
        # If seed device exists and hasn't been processed, try to claim it
        if self.seed_ip and not self._seed_processed.is_set():
            seed_device = self.db.get_device_by_ip(self.seed_ip)
            if seed_device and seed_device['state'] == DeviceState.QUEUED.value:
                if self.db.claim_device(worker_id):
                    self._seed_processed.set()
                    return seed_device
                return None

        # Otherwise, get any queued device
        return self.db.claim_device(worker_id)

    def start(self):
        """Start the crawler with multiple workers."""
        self._cleanup_thread.start()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while not self._stop_event.is_set():
                # Create workers and process devices
                futures = []
                for _ in range(self.max_workers):
                    worker = CrawlerWorker(str(uuid.uuid4()), self.db, self.fsm, self.credentials)
                    device = self._get_next_device(worker.worker_id)
                    if device:
                        futures.append(executor.submit(worker.process_device, device))
                
                # Wait for some workers to complete before claiming more devices
                if futures:
                    for future in futures:
                        future.result()
                else:
                    time.sleep(1)  # No work to do, wait before checking again

    def stop(self):
        """Stop the crawler gracefully."""
        self._stop_event.set()
        self._cleanup_thread.join()

    def _cleanup_stale_claims(self):
        """Periodically clean up stale claims."""
        while not self._stop_event.is_set():
            self.db.cleanup_stale_claims()
            time.sleep(60)  # Check every minute 