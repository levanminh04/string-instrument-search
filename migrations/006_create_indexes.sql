-- ============================================================
-- Migration 006: Indexes
-- ============================================================

-- Index chính cho tìm kiếm similarity (Giai đoạn 1)
-- LƯU Ý: ivfflat cần ≥ 100 rows mới hiệu quả
CREATE INDEX idx_feature_vector_cosine ON audio_files
USING ivfflat (feature_vector vector_cosine_ops)
WITH (lists = 10);

-- Index metadata để filter nhanh
CREATE INDEX idx_instrument ON audio_files (instrument);
CREATE INDEX idx_technique ON audio_files (technique);
CREATE INDEX idx_vector_version ON audio_files (vector_version);
CREATE INDEX idx_pitch_id ON audio_files (pitch_id);
CREATE INDEX idx_dynamics ON audio_files (dynamics);
