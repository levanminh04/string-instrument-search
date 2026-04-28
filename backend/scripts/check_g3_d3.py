import os
import sys
import numpy as np
import librosa

# Add project root to path
sys.path.insert(0, os.getcwd())

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
    
    # Let's also see what Z-score it WOULD have
    # Mean: 63.79, Std: 14.68
    z = (f0_midi - 63.79) / 14.68
    print(f"Z-Score (Approx): {z:.4f}")
    return vec

if __name__ == "__main__":
    check_raw("Contrabass", "contrabass_ord_G3_ff_574.wav")
    check_raw("Contrabass", "contrabass_ord_D3_ff_559.wav")
