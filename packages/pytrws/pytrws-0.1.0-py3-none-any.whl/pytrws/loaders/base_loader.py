from abc import ABC, abstractmethod

class BaseLoader(ABC):
    """Abstract interface for all PyTRWS data loaders."""
    
    @abstractmethod
    def load(self, file_path: str) -> bytes:
        pass
