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


def extract_feature_vector(file_path: str, version: int = 2) -> tuple[np.ndarray, np.ndarray, float, float]:
    """
    Trích xuất vector đặc trưng kiến trúc Multi-Vector (Pitch 3D + Timbre 18D).
    
    Trả về:
    - pitch_vector (3D): F0 MIDI x3
    - timbre_vector (18D): MFCC Mean (10), Contrast (4), MFCC Std (4)
    - rms_mean (1D): Cường độ âm thanh (để hiển thị UI, không đưa vào vector search)
    - actual_extract_sec (float): Thời gian trích xuất thực tế
    """
    # --------- Bước 1: Tiền xử lý ---------
    y, sr = load_and_preprocess(file_path)
    actual_extract_sec = len(y) / sr

    # --------- Bước 2: Trích xuất các thành phần ---------
    mfcc_mean, mfcc_std = compute_mfcc_mean_std(y, sr)
    f0_hz = compute_f0_median(y, sr)
    rms_mean = compute_rms_mean(y)
    contrast_mean = compute_spectral_contrast_mean(y, sr)

    # Chuyển F0 Hz -> MIDI (thang logarithmic đều đặn). Nếu unvoiced (f0=0) -> MIDI=0
    f0_midi = float(librosa.hz_to_midi(f0_hz)) if f0_hz > 0 else 0.0

    # --------- Bước 3: Ghép Vector ---------
    pitch_vector = np.array([f0_midi], dtype=np.float32)
    
    timbre_vector = np.concatenate([
        mfcc_mean[1:11],        # 10 chiều: MFCC Mean C1-C10 (bỏ C0=log energy)
        contrast_mean[0:4],     # 4 chiều: Spectral Contrast B1-B4
        mfcc_std[1:5],          # 4 chiều: MFCC Std C1-C4 (kết cấu timbral)
    ]).astype(np.float32)

    return pitch_vector, timbre_vector, float(rms_mean), float(actual_extract_sec)
