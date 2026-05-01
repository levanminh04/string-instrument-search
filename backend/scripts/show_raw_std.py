import os
import sys
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_connection

def show_raw_std():
    conn = get_connection()
    cur = conn.cursor()
    
    # Get std_vec from scaler_params (version 1)
    cur.execute("SELECT std_vec, n_samples FROM scaler_params WHERE version = 1")
    row = cur.fetchone()
    conn.close()

    if not row:
        print("No scaler params found in DB. Please run fit_scaler.py first.")
        return

    std_vec = row[0]
    n_samples = row[1]

    # Feature names based on extractor.py
    feature_names = [
        "MFCC Mean C1", "MFCC Mean C2", "MFCC Mean C3", "MFCC Mean C4", "MFCC Mean C5",
        "MFCC Mean C6", "MFCC Mean C7", "MFCC Mean C8", "MFCC Mean C9", "MFCC Mean C10",
        "F0 MIDI (Rep 1)", "F0 MIDI (Rep 2)", "F0 MIDI (Rep 3)",
        "RMS Mean (Loudness)",
        "Spectral Contrast B1", "Spectral Contrast B2", "Spectral Contrast B3", "Spectral Contrast B4",
        "MFCC Std C1", "MFCC Std C2", "MFCC Std C3", "MFCC Std C4",
        "Attack Time"
    ]

    print("="*70)
    print(f"RAW STANDARD DEVIATION (STD) - Based on {n_samples} samples")
    print("="*70)
    print(f"{'Index':<5} | {'Feature Name':<25} | {'Raw STD Value':<15}")
    print("-" * 70)

    for i, std_val in enumerate(std_vec):
        name = feature_names[i] if i < len(feature_names) else f"Unknown Dim {i}"
        print(f"{i:<5} | {name:<25} | {std_val:>15.6f}")
    
    print("-" * 70)
    print("Note: Higher STD means the feature has more variation across the dataset.")

if __name__ == "__main__":
    show_raw_std()
