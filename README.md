# String Instrument Audio Retrieval System

Hệ thống CSDL lưu trữ và tìm kiếm tiếng nhạc cụ bộ dây.

## Cấu trúc dự án

```
CSDLDPT/
├── backend/                     # Logic xử lý phía server
│   ├── config.py                # Cấu hình hằng số, DSP params
│   ├── database.py              # Kết nối PostgreSQL
│   ├── features/                # Module trích xuất đặc trưng
│   │   ├── preprocessor.py      # Load, trim, resample
│   │   ├── temporal.py          # Attack, Decay, ZCR, RMS
│   │   ├── spectral.py          # Centroid, Contrast, Rolloff...
│   │   ├── cepstral.py          # MFCC, Delta MFCC
│   │   └── extractor.py         # Ghép thành vector 37/56 chiều
│   ├── search/                  # Module tìm kiếm
│   │   ├── normalizer.py        # Z-Score + L2
│   │   └── similarity.py        # Cosine similarity via pgvector
│   └── scripts/                 # Scripts chạy 1 lần
│       ├── batch_extract.py     # Extract toàn bộ dataset
│       └── fit_scaler.py        # Fit + normalize vectors
│
├── dataset/                     # Bộ dữ liệu TinySOL (1193 files)
│   ├── Violin/
│   ├── Viola/
│   ├── Violoncello/
│   ├── Contrabass/
│   └── metadata.csv
│
├── frontend/                    # Giao diện web
├── migrations/                  # SQL migration scripts
├── uploads/                     # File tạm khi search
└── requirements.txt
```

## Khởi chạy

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Tạo database PostgreSQL + pgvector
createdb string_instrument_db

# 3. Chạy migrations
python -c "from backend.database import run_migrations; run_migrations('migrations')"

# 4. Extract features toàn bộ dataset
python backend/scripts/batch_extract.py

# 5. Fit scaler + normalize vectors
python backend/scripts/fit_scaler.py
```
