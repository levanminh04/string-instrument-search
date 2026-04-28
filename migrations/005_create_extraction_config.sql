-- ============================================================
-- Migration 005: Bảng extraction_config
-- Lưu tham số DSP + danh sách đặc trưng theo thứ tự
-- ============================================================
CREATE TABLE IF NOT EXISTS extraction_config (
    id          SERIAL PRIMARY KEY,
    version     INT NOT NULL UNIQUE,
    frame_size  INT DEFAULT 2048,
    hop_size    INT DEFAULT 512,
    sample_rate INT DEFAULT 22050,
    n_mels      INT DEFAULT 40,
    n_mfcc      INT DEFAULT 13,
    trim_db     FLOAT DEFAULT 20,
    features    TEXT[],                  -- danh sách tên đặc trưng theo thứ tự
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Insert cấu hình Giai đoạn 1 (37 chiều)
INSERT INTO extraction_config (version, features) VALUES (
    1,
    ARRAY[
        'attack_time',
        'mfcc_mean_1','mfcc_mean_2','mfcc_mean_3','mfcc_mean_4','mfcc_mean_5',
        'mfcc_mean_6','mfcc_mean_7','mfcc_mean_8','mfcc_mean_9','mfcc_mean_10',
        'mfcc_mean_11','mfcc_mean_12','mfcc_mean_13',
        'mfcc_std_1','mfcc_std_2','mfcc_std_3','mfcc_std_4','mfcc_std_5',
        'mfcc_std_6','mfcc_std_7','mfcc_std_8','mfcc_std_9','mfcc_std_10',
        'mfcc_std_11','mfcc_std_12','mfcc_std_13',
        'contrast_1','contrast_2','contrast_3','contrast_4',
        'contrast_5','contrast_6','contrast_7',
        'spectral_centroid','zcr','rms_std'
    ]
);
