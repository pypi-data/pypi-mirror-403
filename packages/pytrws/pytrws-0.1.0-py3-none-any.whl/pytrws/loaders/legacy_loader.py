from .base_loader import BaseLoader

class LegacyLoader(BaseLoader):
    """Loader for binary formats: WAD, ELF, EXE, etc."""
    
    def load(self, file_path: str) -> bytes:
        with open(file_path, 'rb') as f:
            # Raw binary read - no encoding, just pure data
            return f.read()
