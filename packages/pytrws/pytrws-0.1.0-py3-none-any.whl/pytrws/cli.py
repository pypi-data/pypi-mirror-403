import sys
import argparse
from pytrws import PyTRWS, __version__

def main():
    parser = argparse.ArgumentParser(
        description=f"PyTRWS v{__version__} - O Vazio Absoluto (by MurilooPrDev)",
        epilog="Se o código é sagrado, o espaço em branco é a sua alma."
    )
    
    parser.add_argument("input", help="Arquivo de entrada (Python, C++, Elf, WAD, etc.)")
    parser.add_argument("-o", "--output", help="Arquivo de saída (padrão: arquivo.ws)")
    parser.add_argument("-v", "--version", action="version", version=f"PyTRWS {__version__}")

    args = parser.parse_args()

    # Se você for burro e não passar nada, o argparse já reclama. 
    # Mas vamos garantir que a execução seja estilosa.
    try:
        engine = PyTRWS()
        print(f"--- Starting PyTRWS Engine ---")
        engine.save_void(args.input, args.output)
        print(f"--- Success. Code is now invisible. ---")
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
