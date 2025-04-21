from enum import Enum, auto
from typing import Optional, Set
from dataclasses import dataclass
from datetime import datetime

class DeviceState(Enum):
    QUEUED = auto()
    CONNECTING = auto()
    COLLECTING = auto()
    DISCOVERED = auto()
    ENRICHED = auto()
    DONE = auto()
    ERROR = auto()

@dataclass
class StateTransition:
    from_state: DeviceState
    to_state: DeviceState
    timestamp: datetime
    error_msg: Optional[str] = None

class DeviceFSM:
    _valid_transitions = {
        DeviceState.QUEUED: {DeviceState.CONNECTING},
        DeviceState.CONNECTING: {DeviceState.COLLECTING, DeviceState.ERROR},
        DeviceState.COLLECTING: {DeviceState.DISCOVERED, DeviceState.ERROR},
        DeviceState.DISCOVERED: {DeviceState.ENRICHED, DeviceState.DONE, DeviceState.ERROR},
        DeviceState.ENRICHED: {DeviceState.DONE, DeviceState.ERROR},
        DeviceState.DONE: set(),
        DeviceState.ERROR: {DeviceState.QUEUED}  # Allow retry from error state
    }

    @classmethod
    def is_valid_transition(cls, from_state: DeviceState, to_state: DeviceState) -> bool:
        """Check if a state transition is valid."""
        return to_state in cls._valid_transitions.get(from_state, set())

    @classmethod
    def get_valid_transitions(cls, state: DeviceState) -> Set[DeviceState]:
        """Get all valid transitions from a given state."""
        return cls._valid_transitions.get(state, set())

    @classmethod
    def create_transition(cls, from_state: DeviceState, to_state: DeviceState, 
                         error_msg: Optional[str] = None) -> StateTransition:
        """Create a new state transition with validation."""
        if not cls.is_valid_transition(from_state, to_state):
            raise ValueError(f"Invalid transition from {from_state} to {to_state}")
        
        return StateTransition(
            from_state=from_state,
            to_state=to_state,
            timestamp=datetime.utcnow(),
            error_msg=error_msg
        ) 