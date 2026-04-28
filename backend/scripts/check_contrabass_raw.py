import os
import sys
import numpy as np
import librosa

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.features.extractor import extract_feature_vector
from backend.config import DATASET_DIR

def check_raw(instrument, filename):
    file_path = os.path.join(DATASET_DIR, instrument, filename)
    print(f"\n--- Raw Extraction: {filename} ---")
    if not os.path.exists(file_path):
        # Try without instrument subfolder just in case
        file_path = os.path.join(DATASET_DIR, filename)
        if not os.path.exists(file_path):
            print(f"File not found: {filename}")
            return None
    
    vec, sec = extract_feature_vector(file_path)
    # Pitch is at indices [10, 11, 12]
    f0_midi = vec[10]
    note = librosa.midi_to_note(f0_midi) if f0_midi > 0 else "N/A"
    print(f"Detected MIDI: {f0_midi:.2f} ({note})")
    print(f"RMS Mean (Loudness): {vec[13]:.6f}")
    print(f"Attack Time: {vec[22]:.4f}s")
    return vec

if __name__ == "__main__":
    # Query
    v1 = check_raw("Contrabass", "contrabass_ord_F3_mf_465.wav")
    # #2 (High similarity but different pitch in metadata)
    v2 = check_raw("Contrabass", "contrabass_ord_D#3_ff_562.wav")
    # #6 (Low similarity but same pitch in metadata)
    v3 = check_raw("Contrabass", "contrabass_ord_F3_pp_361.wav")
