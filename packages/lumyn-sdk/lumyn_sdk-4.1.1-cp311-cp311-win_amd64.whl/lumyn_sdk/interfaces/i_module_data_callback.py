"""
Interface for module data handling callbacks
"""

from abc import ABC, abstractmethod
from typing import Protocol
from ..domain.module.new_data_info import NewDataInfo


class IModuleDataCallback(ABC):
    """Interface for handling module data from the device
    
    This interface mirrors the Java vendordep IModuleDataCallback interface.
    Implement this interface to receive data from modules.
    """
    
    @abstractmethod
    def handle_data(self, data: NewDataInfo) -> None:
        """Handle new data from a module
        
        Args:
            data: NewDataInfo object containing module data
        """
        pass
