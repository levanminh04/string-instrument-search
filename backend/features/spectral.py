"""
Trích xuất đặc trưng phổ tần số (Spectral Domain Features):
- Spectral Centroid
- Spectral Contrast
- Spectral Rolloff (Giai đoạn 2)
- Spectral Bandwidth (Giai đoạn 2)
- Spectral Flatness (Giai đoạn 2)
"""
import numpy as np
import librosa
from backend.config import FRAME_SIZE, HOP_SIZE, SAMPLE_RATE


def compute_spectral_contrast_mean(y: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Spectral Contrast trung bình trên 7 dải tần (7 chiều)."""
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)
    return np.mean(contrast, axis=1)  # shape = (7,)


