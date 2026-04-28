"""
Hàm chính: Ghép tất cả module lại thành 1 vector hoàn chỉnh.
"""
import numpy as np
import librosa
from backend.features.preprocessor import load_and_preprocess
from backend.features.temporal import (
    compute_attack_time,
    compute_rms_mean,
    compute_f0_median,
)
from backend.features.spectral import compute_spectral_contrast_mean
from backend.features.cepstral import compute_mfcc_mean_std


def extract_feature_vector(file_path: str, version: int = 1) -> tuple[np.ndarray, float]:
    """
    Trích xuất vector đặc trưng 23 chiều tối ưu cho TinySOL.

    Cấu trúc 23 chiều:
    - [0-9]:   MFCC Mean C1-C10  (10 dim) → Nhạc cụ (Timbre)
    - [10-12]: F0 MIDI ×3        ( 3 dim) → Cao độ (feature repetition để tăng trọng số)
    - [13]:    RMS Mean           ( 1 dim) → Cường độ (pp/mf/ff)
    - [14-17]: Spectral Contrast B1-B4 ( 4 dim) → Sắc thái hài
    - [18-21]: MFCC Std C1-C4    ( 4 dim) → Kết cấu timbral
    - [22]:    Attack Time        ( 1 dim) → Khởi phát
    """
    # --------- Bước 1: Tiền xử lý ---------
    y, sr = load_and_preprocess(file_path)
    actual_extract_sec = len(y) / sr

    # --------- Bước 2: Trích xuất các thành phần ---------
    mfcc_mean, mfcc_std = compute_mfcc_mean_std(y, sr)
    f0_hz = compute_f0_median(y, sr)
    rms_mean = compute_rms_mean(y)
    contrast_mean = compute_spectral_contrast_mean(y, sr)
    attack_time = compute_attack_time(y, sr)

    # Chuyển F0 Hz → MIDI (thang logarithmic đều đặn). Nếu unvoiced (f0=0) → MIDI=0
    f0_midi = float(librosa.hz_to_midi(f0_hz)) if f0_hz > 0 else 0.0

    # --------- Bước 3: Ghép Vector 23 chiều ---------
    vector_23d = np.concatenate([
        mfcc_mean[1:11],        # 10 chiều: MFCC Mean C1-C10 (bỏ C0=log energy)
        [f0_midi, f0_midi, f0_midi],  # 3 chiều: F0 MIDI ×3 (tăng trọng số pitch)
        [rms_mean],             # 1 chiều: RMS Mean (loudness)
        contrast_mean[0:4],     # 4 chiều: Spectral Contrast B1-B4
        mfcc_std[1:5],          # 4 chiều: MFCC Std C1-C4 (kết cấu timbral)
        [attack_time],          # 1 chiều: Attack Time
    ])

    return vector_23d, float(actual_extract_sec)
