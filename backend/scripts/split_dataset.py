import os
import sys
import random
import shutil

# Thêm path để import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.config import DATASET_DIR, BASE_DIR

TEST_DATASET_DIR = os.path.join(BASE_DIR, "test_dataset")

def restore_100_percent():
    """Gôm toàn bộ file từ test_dataset trả về dataset để dùng 100%"""
    if not os.path.exists(TEST_DATASET_DIR):
        print("✅ Không có thư mục test_dataset. Dữ liệu hiện đang là 100% ở gốc.")
        return

    moved_back = 0
    for instrument in os.listdir(TEST_DATASET_DIR):
        test_instrument_path = os.path.join(TEST_DATASET_DIR, instrument)
        main_instrument_path = os.path.join(DATASET_DIR, instrument)
        
        if not os.path.isdir(test_instrument_path):
            continue
            
        os.makedirs(main_instrument_path, exist_ok=True)
        
        for wav_file in os.listdir(test_instrument_path):
            if wav_file.endswith(".wav"):
                src = os.path.join(test_instrument_path, wav_file)
                dst = os.path.join(main_instrument_path, wav_file)
                shutil.move(src, dst)
                moved_back += 1
                
    # Xoá luôn thư mục test_dataset vì đã rỗng
    shutil.rmtree(TEST_DATASET_DIR)
    
    print("-" * 40)
    print(f"🔄 [CÔNG TẮC 100%]: Đã di chuyển NGƯỢC {moved_back} file về lại thư mục gốc!")
    print("Bây giờ bạn có thể nạp toàn bộ 1193 file vào Database.")

def split_70_30(seed=42):
    """Cắt chuyển 30% file sang test_dataset để nạp 70%"""
    # Bước an toàn: Lấy lại 100% trước khi chia để tránh chia bị lắt nhắt nhiều lần
    restore_100_percent()
    
    random.seed(seed)
    os.makedirs(TEST_DATASET_DIR, exist_ok=True)
    
    total_moved = 0
    total_kept = 0
    
    for instrument in sorted(os.listdir(DATASET_DIR)):
        instrument_path = os.path.join(DATASET_DIR, instrument)
        if not os.path.isdir(instrument_path) or instrument.startswith("."):
            continue
            
        test_instrument_path = os.path.join(TEST_DATASET_DIR, instrument)
        os.makedirs(test_instrument_path, exist_ok=True)
        
        wav_files = sorted([f for f in os.listdir(instrument_path) if f.endswith(".wav")])
        if not wav_files:
            continue
            
        random.shuffle(wav_files)
        
        split_idx = int(len(wav_files) * 0.7)
        train_files = wav_files[:split_idx]
        test_files = wav_files[split_idx:]
        
        # Di chuyển test files (CUT)
        for test_file in test_files:
            src = os.path.join(instrument_path, test_file)
            dst = os.path.join(test_instrument_path, test_file)
            shutil.move(src, dst)
            
        total_kept += len(train_files)
        total_moved += len(test_files)
        
    print("-" * 40)
    print(f"✂️ [CÔNG TẮC 70%]: Đã CHUYỂN đi {total_moved} file làm Test, Giữ lại {total_kept} file làm Train (database).")
    print(f"Thư mục Test ở ngoài Database: {TEST_DATASET_DIR}")

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["all", "split"]:
        print("Sử dụng CÔNG TẮC bằng cách gõ:")
        print("👉 python backend/scripts/split_dataset.py all    (Để nạp 100% dữ liệu)")
        print("👉 python backend/scripts/split_dataset.py split  (Để cắt 30% đem ra test riêng, nạp 70%)")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "all":
        restore_100_percent()
    elif cmd == "split":
        split_70_30()
    
    print("\n[BƯỚC TIẾP THEO]:")
    print("Nhớ Cập nhật DB sau gạt công tắc, hãy chạy:")
    print("1. python -m backend.scripts.batch_extract")
    print("2. python -m backend.scripts.fit_scaler")
