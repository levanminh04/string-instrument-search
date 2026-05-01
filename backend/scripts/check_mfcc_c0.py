"""
Script to check MFCC C0 (Log-Energy) values for the entire dataset.
Helps detect faulty files (silent or extremely loud) that might skew the Scaler.
"""
import os
import sys
import numpy as np
import librosa
import matplotlib.pyplot as plt

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_connection
from backend.features.preprocessor import load_and_preprocess
from backend.config import FRAME_SIZE, HOP_SIZE, N_MELS

def check_mfcc_c0():
    print("="*60)
    print("  SEARCH: CHECKING MFCC C0 (LOG ENERGY) FOR DATASET")
    print("="*60)

    conn = get_connection()
    cur = conn.cursor()

    # 1. Get file list from DB
    cur.execute("SELECT id, file_name, file_path FROM audio_files")
    rows = cur.fetchall()
    
    if not rows:
        print("  ERROR: No data in DB. Run batch_extract.py first.")
        return

    c0_values = []
    results = []

    print(f"  Batch processing {len(rows)} files...")

    for i, (row_id, file_name, file_path) in enumerate(rows):
        try:
            # 2. Load and extract MFCC C0
            if not os.path.isabs(file_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                file_path = os.path.join(base_dir, file_path)

            y, sr = load_and_preprocess(file_path)
            
            mfcc = librosa.feature.mfcc(
                y=y, sr=sr,
                n_mfcc=13,
                n_mels=N_MELS,
                n_fft=FRAME_SIZE,
                hop_length=HOP_SIZE
            )
            
            # C0 is the mean of the first coefficient (index 0) over time
            c0_mean = np.mean(mfcc[0, :])
            
            c0_values.append(c0_mean)
            results.append({
                "id": row_id,
                "name": file_name,
                "c0": c0_mean
            })

            if (i + 1) % 100 == 0:
                print(f"  Done {i + 1}/{len(rows)} files...")

        except Exception as e:
            print(f"  Error processing {file_name}: {e}")

    if not c0_values:
        print("  ERROR: No values extracted.")
        return

    # 3. Calculate statistics
    c0_array = np.array(c0_values)
    mean_val = np.mean(c0_array)
    std_val = np.std(c0_array)
    min_val = np.min(c0_array)
    max_val = np.max(c0_array)

    print("\n" + "="*30)
    print("STATISTICS MFCC C0:")
    print(f"   - Mean: {mean_val:.2f}")
    print(f"   - Std:  {std_val:.2f}")
    print(f"   - Min:  {min_val:.2f}")
    print(f"   - Max:  {max_val:.2f}")
    print("="*30)

    # 4. Find Outliers (3-sigma rule)
    print("\nWARNING: LOW C0 DETECTED (Possibly silence):")
    lower_bound = mean_val - 3 * std_val
    outliers = [r for r in results if r["c0"] < lower_bound]
    
    if not outliers:
        print("   OK: No serious outliers found.")
    else:
        for o in sorted(outliers, key=lambda x: x["c0"]):
            print(f"   - ID {o['id']}: {o['name']} (C0 = {o['c0']:.2f})")

    # 5. Plot distribution
    try:
        plt.figure(figsize=(10, 6))
        plt.hist(c0_array, bins=50, color='skyblue', edgecolor='black')
        plt.axvline(mean_val, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean_val:.2f}')
        plt.title('Distribution of MFCC C0 in Dataset')
        plt.xlabel('C0 Value (Log-Energy)')
        plt.ylabel('Frequency')
        plt.legend()
        plt.grid(axis='y', alpha=0.75)
        
        output_img = "c0_distribution.png"
        plt.savefig(output_img)
        print(f"\nSaved distribution plot to: {output_img}")
    except Exception as e:
        print(f"\nCould not generate plot: {e}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    check_mfcc_c0()
