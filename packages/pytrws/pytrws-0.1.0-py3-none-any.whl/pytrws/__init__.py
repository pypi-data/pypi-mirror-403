__version__ = "0.1.0"
__author__ = "MurilooPrDev"

from .core.translator import WhitespaceEngine
from pathlib import Path

class PyTRWS:
    """
    Main PyTRWS Engine. 
    Handles the transformation of sacred code into the void.
    """
    def __init__(self):
        self.engine = WhitespaceEngine()

    def translate(self, input_path: str):
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        
        data = path.read_bytes()
        return self.engine.encode(data)

    def save_void(self, input_path: str, output_path: str = None):
        if output_path is None:
            output_path = f"{input_path}.ws"
        
        result = self.translate(input_path)
        with open(output_path, "w") as f:
            f.write(result)
        print(f"[*] Void saved to: {output_path}")
