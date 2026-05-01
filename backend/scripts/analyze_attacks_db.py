import os
import sys
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_connection
from backend.features.preprocessor import load_and_preprocess
from backend.features.temporal import compute_attack_time

def analyze_attacks():
    conn = get_connection()
    print("  Loading file list from DB...")
    query = "SELECT instrument, file_path FROM audio_files"
    
    try:
        df_files = pd.read_sql(query, conn)
    except Exception as e:
        print(f"Error reading DB: {e}")
        return
    finally:
        conn.close()

    if df_files.empty:
        print("Database is empty.")
        return

    # Extract raw attack_time (in seconds) to make the "> 1s" check meaningful
    print(f"  Extracting raw attack_time for {len(df_files)} files (this may take a minute)...")
    attacks = []
    
    # Get base directory for relative paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    for i, path in enumerate(df_files['file_path']):
        try:
            full_path = path
            if not os.path.isabs(path):
                full_path = os.path.join(base_dir, path)
                
            y, sr = load_and_preprocess(full_path)
            attack = compute_attack_time(y, sr)
            attacks.append(attack)
        except:
            attacks.append(np.nan)
        
        if (i+1) % 200 == 0:
            print(f"  Processed {i+1}/{len(df_files)} files...")

    df_files['attack_time'] = attacks
    df = df_files.dropna()

    print("\n" + "="*60)
    print(f"{'INSTRUMENT':<15} | {'STD (s)':<10} | {'% ATTACK > 1s'}")
    print("-" * 60)

    # YOUR CODE SNIPPET:
    for instrument in ["Violin", "Viola", "Violoncello", "Contrabass"]:
        # Filter by instrument
        instrument_data = df[df["instrument"].str.lower() == instrument.lower()]
        subset = instrument_data["attack_time"]
        
        if subset.empty:
            print(f"{instrument:<15} | No data")
            continue
            
        std_val = subset.std()
        # Calculate percentage of files with attack_time > 1.0s
        # (subset > 1) returns a boolean series, .mean() gives the ratio
        error_percentage = (subset > 1).mean() * 100
        
        print(f"{instrument:<15} | {std_val:.3f}      | {error_percentage:.1f}%")
    print("-" * 60)

if __name__ == "__main__":
    analyze_attacks()
