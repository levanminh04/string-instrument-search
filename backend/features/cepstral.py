"""
Trích xuất đặc trưng Cepstral (MFCC):
- MFCC Mean (13 chiều)
- MFCC Std (13 chiều)
- Delta MFCC Std (13 chiều — Giai đoạn 2)
"""
import numpy as np
import librosa
from backend.config import FRAME_SIZE, HOP_SIZE, N_MELS, N_MFCC, SAMPLE_RATE


def compute_mfcc_mean_std(y: np.ndarray, sr: int = SAMPLE_RATE) -> tuple[np.ndarray, np.ndarray]:
    """
    Trả về MFCC Mean (13 chiều) và MFCC Std (13 chiều).

    Returns:
        mfcc_mean: shape (13,)
        mfcc_std: shape (13,)
    """
    mfcc = librosa.feature.mfcc(
        y=y, sr=sr,
        n_mfcc=N_MFCC,
        n_mels=N_MELS,
        n_fft=FRAME_SIZE,
        hop_length=HOP_SIZE,
    )
    mfcc_mean = np.mean(mfcc, axis=1)  # shape = (13,)
    mfcc_std = np.std(mfcc, axis=1)    # shape = (13,)
    return mfcc_mean, mfcc_std
