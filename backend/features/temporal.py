"""
Trích xuất đặc trưng thời gian (Temporal Domain Features):
- Attack Time
- Decay Time (Giai đoạn 2)
- ZCR (Zero-Crossing Rate)
- RMS Energy (Std + Mean)
- Silence Ratio (Giai đoạn 2)
"""
import numpy as np
import librosa
from backend.config import FRAME_SIZE, HOP_SIZE


def compute_attack_time(y: np.ndarray, sr: int) -> float:
    """Thời gian từ onset đến peak amplitude (giây)."""
    rms = librosa.feature.rms(y=y, frame_length=FRAME_SIZE, hop_length=HOP_SIZE)[0]
    peak_idx = np.argmax(rms)
    peak_val = rms[peak_idx]

    # Tìm onset: frame đầu tiên vượt 20% peak
    threshold = 0.2 * peak_val
    onset_idx = 0
    for i in range(peak_idx):
        if rms[i] >= threshold:
            onset_idx = i
            break

    attack_time = (peak_idx - onset_idx) * HOP_SIZE / sr
    return float(attack_time)


def compute_decay_time(y: np.ndarray, sr: int) -> float:
    """Thời gian từ peak đến khi amplitude giảm xuống 10% peak (giây)."""
    rms = librosa.feature.rms(y=y, frame_length=FRAME_SIZE, hop_length=HOP_SIZE)[0]
    peak_idx = np.argmax(rms)
    peak_val = rms[peak_idx]

    threshold = 0.1 * peak_val
    offset_idx = len(rms) - 1
    for i in range(peak_idx, len(rms)):
        if rms[i] <= threshold:
            offset_idx = i
            break

    decay_time = (offset_idx - peak_idx) * HOP_SIZE / sr
    return float(decay_time)


def compute_zcr_mean(y: np.ndarray) -> float:
    """Tốc độ đổi dấu trung bình (Zero-Crossing Rate Mean)."""
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=FRAME_SIZE, hop_length=HOP_SIZE)[0]
    return float(np.mean(zcr))


def compute_rms_std(y: np.ndarray) -> float:
    """Độ lệch chuẩn của đường cong âm lượng (RMS Std)."""
    rms = librosa.feature.rms(y=y, frame_length=FRAME_SIZE, hop_length=HOP_SIZE)[0]
    return float(np.std(rms))


def compute_rms_mean(y: np.ndarray) -> float:
    """Trung bình âm lượng (RMS Mean) — Giai đoạn 2."""
    rms = librosa.feature.rms(y=y, frame_length=FRAME_SIZE, hop_length=HOP_SIZE)[0]
    return float(np.mean(rms))


def compute_silence_ratio(y: np.ndarray) -> float:
    """Tỷ lệ khung hình im lặng (< 5% peak RMS) — Giai đoạn 2."""
    rms = librosa.feature.rms(y=y, frame_length=FRAME_SIZE, hop_length=HOP_SIZE)[0]
    peak = np.max(rms)
    if peak == 0:
        return 1.0
    threshold = 0.05 * peak
    silent_frames = np.sum(rms < threshold)
    return float(silent_frames / len(rms))


def compute_f0_median(y: np.ndarray, sr: int) -> float:
    """Tần số cơ bản trung vị F0 (Hz) — dùng librosa.pyin."""
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'),
        sr=sr, frame_length=FRAME_SIZE, hop_length=HOP_SIZE,
    )
    f0_voiced = f0[~np.isnan(f0)]
    if len(f0_voiced) == 0:
        return 0.0
    return float(np.median(f0_voiced))
