-- migration: 015_add_multi_vector
-- Thêm cột pitch_vector(3) và timbre_vector(18) cho kiến trúc Multi-Vector

ALTER TABLE audio_files ADD COLUMN pitch_vector vector(3);
ALTER TABLE audio_files ADD COLUMN timbre_vector vector(18);

-- Pitch dùng Euclidean Distance (L2)
CREATE INDEX idx_pitch_vector ON audio_files USING hnsw (pitch_vector vector_l2_ops) WITH (m = 16, ef_construction = 64);

-- Timbre dùng Cosine Similarity
CREATE INDEX idx_timbre_vector ON audio_files USING hnsw (timbre_vector vector_cosine_ops) WITH (m = 16, ef_construction = 64);
