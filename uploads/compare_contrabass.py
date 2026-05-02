import os
import sys
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import execute_query

def compare_features(query_name, other_name):
    print(f"\n--- Comparing {query_name} vs {other_name} ---")
    
    q = "SELECT file_name, feature_vector FROM audio_files WHERE file_name IN (%s, %s)"
    rows = execute_query(q, (query_name, other_name), fetch=True)
    
    if len(rows) < 2:
        # Check if missing
        existing = [r['file_name'] for r in rows]
        print(f"Required files not found. Only found: {existing}")
        return

    data = {}
    for r in rows:
        vec = r['feature_vector']
        if isinstance(vec, str):
            vec = np.fromstring(vec.strip('[]'), sep=',')
        else:
            vec = np.array(vec)
        data[r['file_name']] = vec
    
    v1 = data.get(query_name)
    v2 = data.get(other_name)
    
    if v1 is None or v2 is None:
        print(f"Failed to load vectors for both files.")
        return
    
    # Ensure they are 1D arrays
    v1 = v1.flatten()
    v2 = v2.flatten()
    
    f_names = [
        "MFCC_M1", "MFCC_M2", "MFCC_M3", "MFCC_M4", "MFCC_M5", "MFCC_M6", "MFCC_M7", "MFCC_M8", "MFCC_M9", "MFCC_M10",
        "PITCH_1", "PITCH_2", "PITCH_3",
        "LOUDNESS",
        "CONTRAST1", "CONTRAST2", "CONTRAST3", "CONTRAST4",
        "MFCC_S1", "MFCC_S2", "MFCC_S3", "MFCC_S4",
        "ATTACK"
    ]
    
    print(f"{'Feature':<15} | {'Query':<10} | {'Other':<10} | {'Abs Diff':<10}")
    print("-" * 55)
    for i, name in enumerate(f_names):
        diff = abs(v1[i] - v2[i])
        print(f"{name:<15} | {v1[i]:>10.4f} | {v2[i]:>10.4f} | {diff:>10.4f}")
    
    cos_sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    print(f"\nCosine Similarity (DB Vectors): {cos_sim*100:.2f}%")

if __name__ == "__main__":
    query = "contrabass_ord_F3_mf_465.wav"
    # Compare with #2 (Ranked high but different pitch)
    compare_features(query, "contrabass_ord_D#3_ff_562.wav")
    # Compare with #6 (Ranked lower but same pitch)
    compare_features(query, "contrabass_ord_F3_pp_361.wav")
