from enum import Enum
from typing import Optional, Set
from dataclasses import dataclass

class DeviceState(Enum):
    QUEUED = "queued"
    CONNECTING = "connecting"
    COLLECTING = "collecting"
    DISCOVERED = "discovered"
    ENRICHED = "enriched"
    DONE = "done"
    ERROR = "error"

@dataclass
class Transition:
    from_state: DeviceState
    to_state: DeviceState
    condition: Optional[str] = None

class DeviceFSM:
    def __init__(self):
        self._transitions = {
            DeviceState.QUEUED: {DeviceState.CONNECTING},
            DeviceState.CONNECTING: {DeviceState.COLLECTING, DeviceState.ERROR},
            DeviceState.COLLECTING: {DeviceState.DISCOVERED, DeviceState.ERROR},
            DeviceState.DISCOVERED: {DeviceState.ENRICHED, DeviceState.DONE, DeviceState.ERROR},
            DeviceState.ENRICHED: {DeviceState.DONE, DeviceState.ERROR},
            DeviceState.DONE: set(),
            DeviceState.ERROR: {DeviceState.QUEUED}
        }

    def is_valid_transition(self, current_state: DeviceState, new_state: DeviceState) -> bool:
        """Check if a state transition is valid."""
        return new_state in self._transitions.get(current_state, set())

    def get_valid_transitions(self, current_state: DeviceState) -> Set[DeviceState]:
        """Get all valid transitions from the current state."""
        return self._transitions.get(current_state, set())

    def can_retry(self, current_state: DeviceState) -> bool:
        """Check if a device in error state can be retried."""
        return current_state == DeviceState.ERROR

    def is_terminal_state(self, state: DeviceState) -> bool:
        """Check if a state is terminal (no further transitions possible)."""
        return state == DeviceState.DONE

    def is_error_state(self, state: DeviceState) -> bool:
        """Check if a state is an error state."""
        return state == DeviceState.ERROR 