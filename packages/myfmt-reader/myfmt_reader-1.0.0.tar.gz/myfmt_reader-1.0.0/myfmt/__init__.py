from .reader import read_myfmt
from .writer import to_myfmt
from .generator import generate_files

__version__ = "1.0.0"

# Auto-generate files on first import
generate_files()