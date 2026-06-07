"""
Tiền xử lý âm thanh: Load, Resample, Trim silence.
"""
import librosa
import numpy as np
from backend.config import SAMPLE_RATE, TRIM_TOP_DB, SKIP_SECONDS, EXTRACT_SECONDS


def load_and_preprocess(file_path: str, skip_seconds: float = SKIP_SECONDS, extract_seconds: float = EXTRACT_SECONDS) -> tuple[np.ndarray, int]:
    """
    Load file âm thanh, chuyển Mono, Resample về 22050Hz, Trim silence, cắt bỏ đoạn đầu và lấy khung cố định.

    Returns:
        y: Mảng tín hiệu âm thanh đã xử lý
        sr: Tần số lấy mẫu (luôn = 22050)
    """
    # 1. Load file, tự động chuyển mono và resample
    y, sr = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)

    # y = librosa.util.normalize(y)  # Đã tắt để giữ nguyên dynamic pp/ff của Ircam

    # 2. Trim silence ở 2 đầu
    y, _ = librosa.effects.trim(y, top_db=TRIM_TOP_DB)

    # 3. Bỏ qua 1s đầu và lấy 3s tiếp theo 
    start_sample = int(skip_seconds * sr)
    end_sample = start_sample + int(extract_seconds * sr)

    # LỆNH BẢO VỆ MẠNG SỐNG:
    # Pizzicato (gảy rụp 1 phát) chiều dài chỉ có 0.5s. Nếu cố tình vứt 1s đầu, mảng sẽ bị RỖNG (len = 0).
    # Tránh làm code crash, nếu file ngắn hơn 1 giây, ta đành lấy từ 0.
    if start_sample >= len(y):
        start_sample = 0
        end_sample = min(len(y), int(extract_seconds * sr))

    y = y[start_sample:min(end_sample, len(y))]

    return y, sr
