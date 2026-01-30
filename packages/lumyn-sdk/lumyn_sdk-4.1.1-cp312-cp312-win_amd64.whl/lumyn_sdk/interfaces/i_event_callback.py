"""
Interface for event handling callbacks
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..domain.event import Event


class IEventCallback(ABC):
    """Interface for handling events from the device
    
    This interface mirrors the Java vendordep IEventCallback interface.
    Implement this interface to receive events from the device.
    """
    
    @abstractmethod
    def handle_event(self, event: 'Event') -> None:
        """Handle an event from the device
        
        Args:
            event: Event object containing event information
        """
        pass
