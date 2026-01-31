import pandas as pd
from datetime import datetime

def to_myfmt(df: pd.DataFrame, file_path: str, author: str = "Unknown") -> None:
    """
    Writes a Pandas DataFrame to a .myfmt file.

    Parameters:
        df (pd.DataFrame): DataFrame to write.
        file_path (str): Output file path.
        author (str): Author name for metadata.
    """
    with open(file_path, 'w') as f:
        # Write META section
        f.write("# ===== META =====\n")
        f.write(f"# format: myfmt\n")
        f.write(f"# version: 1.0\n")
        f.write(f"# author: {author}\n")
        f.write(f"# generated_at: {datetime.now().isoformat()}\n\n")
        
        # Write DATA section header
        f.write("# ===== DATA =====\n")
        f.write(f"# Columns: {', '.join(df.columns)}\n\n")
        
        # Write each row
        for _, row in df.iterrows():
            f.write("---\n")
            for col, value in row.items():
                f.write(f"{col}: {value}\n")
            f.write("\n")