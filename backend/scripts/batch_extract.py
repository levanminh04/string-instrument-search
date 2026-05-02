"""
Script chạy 1 lần: Trích xuất đặc trưng toàn bộ dataset → INSERT vào DB.
Đọc metadata.csv để lấy mô tả chi tiết cho mỗi file.
"""
import os
import sys
import csv
import numpy as np

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.config import DATASET_DIR, METADATA_CSV, PITCH_DIM, TIMBRE_DIM
from backend.features.extractor import extract_feature_vector
from backend.database import get_connection


def load_metadata(csv_path: str) -> dict:
    """Đọc metadata.csv trả về dict {file_name: row_dict}."""
    metadata = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metadata[row["name"]] = row
    return metadata


def batch_extract():
    """Quét toàn bộ dataset, extract feature, INSERT vào audio_files."""
    print("=" * 60)
    print(f"  BATCH EXTRACT — Multi-Vector Architecture (Pitch {PITCH_DIM}D + Timbre {TIMBRE_DIM}D)")
    print("=" * 60)

    # Load metadata
    metadata = load_metadata(METADATA_CSV)
    print(f"  📋 Đã đọc metadata: {len(metadata)} file")

    # Quét thư mục dataset
    conn = get_connection()
    cur = conn.cursor()

    print("  🧹 Đang dọn dẹp Database cũ (TRUNCATE) để nạp mới hoàn toàn...")
    cur.execute("TRUNCATE TABLE audio_files, scaler_params, search_logs RESTART IDENTITY CASCADE;")
    conn.commit()

    count = 0
    errors = []

    for instrument_dir in sorted(os.listdir(DATASET_DIR)):
        instrument_path = os.path.join(DATASET_DIR, instrument_dir)
        if not os.path.isdir(instrument_path) or instrument_dir.startswith("."):
            continue

        for wav_file in sorted(os.listdir(instrument_path)):
            if not wav_file.endswith(".wav"):
                continue

            file_path = os.path.join(instrument_path, wav_file)
            file_name = wav_file

            # Tìm metadata
            meta = metadata.get(file_name, {})

            try:
                # Extract vector và thời gian thực tế đã quét
                raw_pitch, raw_timbre, rms_mean, extract_duration_sec = extract_feature_vector(file_path)

                # INSERT / UPDATE
                cur.execute(
                    f"""
                    INSERT INTO audio_files
                        (file_name, file_path, duration_sec, extract_duration_sec, instrument, technique,
                         pitch, pitch_id, dynamics, dynamics_id, string_id, instance_id,
                         pitch_vector, timbre_vector)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (file_path) DO UPDATE SET
                        extract_duration_sec = EXCLUDED.extract_duration_sec,
                        pitch_vector = EXCLUDED.pitch_vector,
                        timbre_vector = EXCLUDED.timbre_vector
                    """,
                    (
                        file_name,
                        file_path,
                        float(meta.get("duration", 0)),
                        float(extract_duration_sec),
                        meta.get("instrument", instrument_dir),
                        meta.get("technique", "ordinario"),
                        meta.get("pitch"),
                        int(meta["pitch_id"]) if meta.get("pitch_id") else None,
                        meta.get("dynamics"),
                        int(meta["dynamics_id"]) if meta.get("dynamics_id") else None,
                        float(meta["string_id"]) if meta.get("string_id") else None,
                        int(meta["instance_id"]) if meta.get("instance_id") else None,
                        raw_pitch.tolist(),
                        raw_timbre.tolist(),
                    ),
                )

                count += 1
                if count % 50 == 0:
                    print(f"  ✅ Đã xử lý {count} file...")
                    conn.commit()

            except Exception as e:
                errors.append((file_name, str(e)))
                print(f"  ❌ Lỗi: {file_name} — {e}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n  🎉 HOÀN TẤT: {count} file đã INSERT thành công.")
    if errors:
        print(f"  ⚠️  {len(errors)} file bị lỗi:")
        for name, err in errors[:5]:
            print(f"     - {name}: {err}")


if __name__ == "__main__":
    batch_extract()
