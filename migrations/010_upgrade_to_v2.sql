-- ============================================================
-- Migration 010: Upgrade Giai đoạn 1 → 2 (37 chiều → 56 chiều)
-- Chạy SAU KHI đã re-extract toàn bộ file thành vector 56 chiều
-- ============================================================

-- Bước 1: Tạo index cho cột v2
CREATE INDEX idx_feature_vector_v2_cosine ON audio_files
USING ivfflat (feature_vector_v2 vector_cosine_ops)
WITH (lists = 10);

-- Bước 2: Cập nhật version cho tất cả file đã có vector v2
UPDATE audio_files
SET vector_version = 2
WHERE feature_vector_v2 IS NOT NULL;

-- Bước 3: Insert scaler mới (thực hiện từ Python sau khi fit xong)
