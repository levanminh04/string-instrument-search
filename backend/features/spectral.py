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


def compute_spectral_centroid_mean(y: np.ndarray, sr: int = SAMPLE_RATE) -> float:
    """Trọng tâm phổ trung bình (Hz) — điểm thăng bằng bập bênh."""
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)[0]
    return float(np.mean(centroid))


def compute_spectral_contrast_mean(y: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Spectral Contrast trung bình trên 7 dải tần (7 chiều)."""
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)
    return np.mean(contrast, axis=1)  # shape = (7,)


def compute_spectral_rolloff_mean(y: np.ndarray, sr: int = SAMPLE_RATE) -> float:
    """Điểm cắt trần 85% năng lượng (Hz) — Giai đoạn 2."""
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, n_fft=FRAME_SIZE, hop_length=HOP_SIZE, roll_percent=0.85)[0]
    return float(np.mean(rolloff))


def compute_spectral_bandwidth_mean(y: np.ndarray, sr: int = SAMPLE_RATE) -> float:
    """Bề ngang phổ trung bình (Hz) — Giai đoạn 2."""
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)[0]
    return float(np.mean(bandwidth))


def compute_spectral_flatness_mean(y: np.ndarray) -> float:
    """Độ phẳng phổ trung bình [0=nhạc tính, 1=nhiễu trắng] — Giai đoạn 2."""
    flatness = librosa.feature.spectral_flatness(y=y, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)[0]
    return float(np.mean(flatness))
