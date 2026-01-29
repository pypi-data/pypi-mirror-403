class WSFormatter:
    """
    Utilities to beautify or obfuscate the whitespace output.
    Because even invisible code needs style.
    """
    @staticmethod
    def block_format(ws_data: str, width: int = 8) -> str:
        """Groups whitespace bits into blocks for 'readability'."""
        lines = ws_data.split('\n')
        formatted = []
        for line in lines:
            # Grouping bits into chunks
            chunks = [line[i:i+width] for i in range(0, len(line), width)]
            formatted.append(" ".join(chunks))
        return "\n".join(formatted)
