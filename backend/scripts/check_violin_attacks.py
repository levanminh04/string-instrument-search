import os
import sys
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.features.preprocessor import load_and_preprocess
from backend.features.temporal import compute_attack_time
from backend.config import DATASET_DIR

def check_violin_attacks():
    # Chuyển hướng sang thư mục Violin
    v_dir = os.path.join(DATASET_DIR, "Violin")
    if not os.path.exists(v_dir):
        print(f"Directory not found: {v_dir}")
        return

    all_files = [f for f in os.listdir(v_dir) if f.endswith(".wav")]
    all_results = []

    print(f"Analyzing {len(all_files)} Violin files... Printing real-time:")
    print(f"\n{'File Name':<45} | {'Dynamic':<8} | {'Attack (s)':<10}")
    print("-" * 65)
    
    for f in all_files:
        dynamic = None
        for d in ["pp", "mf", "ff"]:
            if f"_{d}_" in f:
                dynamic = d
                break
        if not dynamic: continue

        path = os.path.join(v_dir, f)
        try:
            y, sr = load_and_preprocess(path)
            attack = compute_attack_time(y, sr)
            all_results.append((f, dynamic, attack))
            print(f"{f:<45} | {dynamic:<8} | {attack:>10.4f}")
        except Exception as e:
            continue

    # Summary Statistics
    print(f"\n--- FINAL SUMMARY STATISTICS (VIOLIN) ---")
    print(f"{'Dynamic':<10} | {'Count':<8} | {'Min (s)':<10} | {'Max (s)':<10} | {'Avg (s)':<10}")
    print("-" * 55)
    for d in ["pp", "mf", "ff"]:
        vals = [r[2] for r in all_results if r[1] == d]
        if not vals: continue
        print(f"{d:<10} | {len(vals):<8} | {min(vals):>10.4f} | {max(vals):>10.4f} | {sum(vals)/len(vals):>10.4f}")

if __name__ == "__main__":
    check_violin_attacks()
