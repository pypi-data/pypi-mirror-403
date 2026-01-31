import pandas as pd
import re

def read_myfmt(file_path: str) -> pd.DataFrame:
    """
    Reads a .myfmt file and returns a Pandas DataFrame.

    Parameters:
        file_path (str): Path to the .myfmt file.

    Returns:
        pd.DataFrame
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Extract columns
    columns = []
    data_lines = []
    in_data = False

    for line in lines:
        line = line.strip()
        
        if line.startswith('# ===== DATA ====='):
            in_data = True
            continue
            
        if in_data and line.startswith('# Columns:'):
            # Extract column names
            columns = [col.strip() for col in line.split(':', 1)[1].split(',')]
            continue
            
        if in_data and line == '---':
            continue
            
        if in_data and line and not line.startswith('#'):
            data_lines.append(line)

    # Parse data
    records = []
    record = {}
    
    for line in data_lines:
        if ':' not in line:
            continue
            
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        
        record[key] = value
        
        # If record is complete, add to records and reset
        if len(record) == len(columns):
            records.append(record)
            record = {}
    
    # Handle last record
    if record:
        records.append(record)
    
    # Create DataFrame & convert dtypes
    df = pd.DataFrame(records, columns=columns)
    
    # Try to convert to better dtypes
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')
    
    return df