class WhitespaceEngine:
    """
    High-performance translation engine for PyTRWS.
    Converts binary streams (ELF, WAD, PY, CPP) into invisible whitespace.
    """
    def __init__(self):
        self.SPACE = ' '
        self.TAB = '\t'
        self.LF = '\n'

    def encode(self, data: bytes) -> str:
        """
        Translates raw bytes into an 8-bit whitespace sequence.
        """
        output = []
        for byte in data:
            # Standard binary conversion
            bits = format(byte, '08b')
            # Mapping 0 to Space and 1 to Tab
            ws_sequence = bits.replace('0', self.SPACE).replace('1', self.TAB)
            output.append(ws_sequence)
        
        return self.LF.join(output)

    def decode(self, ws_data: str) -> bytes:
        """
        Reverses the process. Because sometimes you want your code back.
        """
        bytes_list = []
        lines = ws_data.strip().split(self.LF)
        for line in lines:
            if not line: continue
            bit_str = line.replace(self.SPACE, '0').replace(self.TAB, '1')
            bytes_list.append(int(bit_str, 2))
        
        return bytes(bytes_list)
