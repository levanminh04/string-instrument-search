# test_search.py
import sys
import os
from backend.features.extractor import extract_feature_vector
from backend.search.normalizer import normalize_vector
from backend.search.similarity import search_similar

def test_search(wav_path):
    print(f"\n--- Đang tìm kiếm cho file: {os.path.basename(wav_path)} ---")
    
    # 1. Trích xuất đặc trưng thô từ file input (bây giờ trả về tuple)
    raw_vec, extract_dur = extract_feature_vector(wav_path, version=1)
    print(f"  [Info] Thực tế đã trích xuất {extract_dur:.2f} giây âm thanh.")
    
    # 2. Chuẩn hóa Z-score + L2
    clean_vec = normalize_vector(raw_vec, version=1)
    
    # 3. Truy vấn Cosine Similarity trong Database
    results = search_similar(clean_vec, version=1, top_k=6)
    
    print(f"Thời gian search: {results['search_time_ms']} ms")
    print("-" * 50)
    for i, res in enumerate(results['results']):
        print(f"{i+1}. [{res['instrument']}] {res['file_name']} (Độ khớp: {res['similarity']:.4f})")
        print(f"   - Pitch: {res['pitch']}, Dynamics: {res['dynamics']}")

if __name__ == "__main__":
    # BẠN HÃY THAY ĐƯỜNG DẪN 1 FILE CÓ SẴN ĐỂ TEST
    test_file = r"d:\PTIT\kì 2 năm 4\Cơ sở dữ liệu đa phương tiện\CSDLDPT\dataset\Viola\viola_ord_C4_ff_825.wav" 
    
    if os.path.exists(test_file):
        test_search(test_file)
    else:
        print("Lỗi: Không tìm thấy file test. Hãy kiểm tra lại đường dẫn!")
