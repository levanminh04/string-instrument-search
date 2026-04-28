-- ============================================================
-- Migration 002: Bảng chính audio_files
-- Lưu metadata + feature vector cho mỗi file âm thanh
-- ============================================================
CREATE TABLE IF NOT EXISTS audio_files (
    id                SERIAL PRIMARY KEY,

    -- Thông tin file
    file_name         TEXT NOT NULL,
    file_path         TEXT NOT NULL,
    duration_sec      FLOAT,
    sample_rate       INT DEFAULT 22050,

    -- Metadata nhạc cụ (lấy từ TinySOL metadata.csv)
    instrument        TEXT,              -- Violin, Viola, Violoncello, Contrabass
    technique         TEXT,              -- ordinario (kéo vĩ thông thường)

    -- Metadata bổ sung từ TinySOL
    pitch             TEXT,              -- C2, F#5... (tên nốt nhạc)
    pitch_id          INT,               -- Mã MIDI: C4=60, C2=36...
    dynamics          TEXT,              -- pp, mf, ff
    dynamics_id       INT,               -- 0=pp, 2=mf, 4=ff
    string_id         FLOAT,             -- Sợi dây số mấy (1=cao nhất)
    instance_id       INT,               -- Phiên bản thu âm (Take 1, 2...)

    -- F0 metadata (KHÔNG vào vector — xem doc5)
    f0_median_hz      FLOAT,
    f0_range_hz       FLOAT,

    -- Feature vectors
    feature_vector    vector(37),        -- Giai đoạn 1: 37 chiều
    feature_vector_v2 vector(56),        -- Giai đoạn 2: 56 chiều (NULL ban đầu)
    vector_version    INT DEFAULT 1,     -- 1 = dùng feature_vector, 2 = dùng v2

    created_at        TIMESTAMP DEFAULT NOW()
);

-- Ràng buộc: không trùng file
ALTER TABLE audio_files ADD CONSTRAINT uq_file_path UNIQUE (file_path);
