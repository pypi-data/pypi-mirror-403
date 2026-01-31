import os
import pkgutil
from pathlib import Path

EXAMPLE_FILE = "example.myfmt"
README_FILE = "MYFMT_README.md"

def generate_files(directory: str = ".") -> None:
    """
    Generates example files in the specified directory.
    Runs automatically when the package is imported.

    Parameters:
        directory (str): Target directory. Default = Current Directory.
    """
    target_dir = Path(directory)
    
    # Create files only if they DON'T exist
    if not (target_dir / EXAMPLE_FILE).exists():
        # Load example.myfmt from package_data
        data = pkgutil.get_data(__name__, f"data/{EXAMPLE_FILE}")
        with open(target_dir / EXAMPLE_FILE, 'wb') as f:
            f.write(data)
        print(f"✅ Created: {target_dir / EXAMPLE_FILE}")
    
    if not (target_dir / README_FILE).exists():
        data = pkgutil.get_data(__name__, f"data/{README_FILE}")
        with open(target_dir / README_FILE, 'wb') as f:
            f.write(data)
        print(f"✅ Created: {target_dir / README_FILE}")