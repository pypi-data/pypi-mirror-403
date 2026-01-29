from .base_loader import BaseLoader

class PythonLoader(BaseLoader):
    """Loader specifically for Python source files."""
    
    def load(self, file_path: str) -> bytes:
        with open(file_path, 'r', encoding='utf-8') as f:
            # We treat Python as UTF-8 but return bytes for the engine
            return f.read().encode('utf-8')
