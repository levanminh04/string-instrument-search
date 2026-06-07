"""
Cấu hình hằng số và biến môi trường cho hệ thống.
"""
import os

# ============================================================
# Database PostgreSQL
# ============================================================
DB_HOST = os.getenv("DB_HOST", "15.134.248.39")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "audiostring_db")
DB_USER = os.getenv("DB_USER", "user1")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ============================================================
# Đường dẫn thư mục
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
METADATA_CSV = os.path.join(DATASET_DIR, "metadata.csv")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# Tạo thư mục uploads nếu chưa có
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================
# Tham số DSP (Digital Signal Processing)
# ============================================================
SAMPLE_RATE = 22050
FRAME_SIZE = 2048
HOP_SIZE = 512
N_MELS = 40
N_MFCC = 13
TRIM_TOP_DB = 60         # NGƯỠNG NHẠY: Bắt được cả tiếng miết vĩ siêu nhẹ (TinySOL)
SKIP_SECONDS = 0.0       # Lấy từ đầu (sau trim silence) để bắt trọn tín hiệu nốt nhạc
EXTRACT_SECONDS = 3.0    

# ============================================================
# Feature Vector (Multi-Vector Architecture)
# ============================================================
PITCH_DIM = 1
TIMBRE_DIM = 18

FEATURE_NAMES_PITCH = ["f0_midi"]

FEATURE_NAMES_TIMBRE = [
    *[f"mfcc_mean_{i}" for i in range(1, 11)],  # [0-9]   MFCC Mean C1-C10
    *[f"contrast_{i}" for i in range(1, 5)],     # [10-13] Spectral Contrast B1-B4
    *[f"mfcc_std_{i}" for i in range(1, 5)],     # [14-17] MFCC Std C1-C4
]

# ============================================================
# Tìm kiếm
# ============================================================
TOP_K = 5                # Số kết quả trả về
