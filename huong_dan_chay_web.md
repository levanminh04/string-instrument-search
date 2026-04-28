# HƯỚNG DẪN CHẠY VÀ TEST HỆ THỐNG TIMBRE SONAR

Tài liệu này hướng dẫn cách khởi động lại toàn bộ hệ thống từ con số 0, cách chạy giao diện Web, và giải đáp chuyên sâu về giới hạn của thuật toán nhận diện.

---

## PHẦN 1: QUY TRÌNH KHỞI ĐỘNG HỆ THỐNG (Dành cho việc chấm điểm Demo)

Nếu bạn thay đổi cấu hình, thêm file mới vào thư mục dataset, hoặc muốn reset lại hệ thống để bảo vệ đồ án, hãy chạy tuần tự 4 lệnh sau trong Terminal (đảm bảo đang đứng ở thư mục gốc `CSDLDPT`):

### Bước 1: Khởi tạo/Cập nhật Database
Tạo các bảng, views và indexes nếu chưa có (lệnh này rất an toàn, có thể chạy lại nhiều lần).
```bash
python -c "from backend.database import run_migrations; run_migrations('migrations')"
```

### Bước 2: Trích xuất đặc trưng (Nạp dữ liệu thô)
Quét toàn bộ thư mục `dataset/`, tính toán vector 37 chiều (hoặc 56 chiều) cho từng file âm thanh và lưu vào Database. Trong code đã cài cắm tự động làm sạch (Truncate) bảng cũ để nạp cái mới.
```bash
python backend/scripts/batch_extract.py
```

### Bước 3: Huấn luyện bộ Chuẩn hóa (Fit Scaler)
Việc tìm kiếm bằng khoảng cách Cosine bắt buộc các con số phải cùng chung một hệ trục tọa độ (Ví dụ: Attack Time từ [0, 3] giây phải chung mâm với Spectral Centroid từ [500, 3000] Hz). Lệnh này sẽ tính Mean/Std của toàn bộ cột dữ liệu và đưa chúng về phân phối chuẩn (Z-Score).
```bash
python backend/scripts/fit_scaler.py
```

### Bước 4: Khởi động Web Server (FastAPI + Giao diện UI)
Mở cổng kết nối để giao diện Web Vanilla JS có thể gọi lệnh xuống Backend.
```bash
python -m uvicorn backend.main:app --reload
```
👉 Cuối cùng, mở trình duyệt và truy cập: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## PHẦN 2: THỰC TẾ KIỂM THỬ VÀ LÝ LUẬN VỀ VẤN ĐỀ "BẢN NHẠC CELLO RA CONTRABASS"

Bạn đã đặt ra một câu hỏi cực kỳ xuất sắc: **"Nếu tôi nâng cấp từ Vector 37 chiều (V1) lên 56 chiều (V2) thì nó có giải quyết được việc cho một đoạn nhạc Cello nhiều nốt vào bị nhận diện nhầm thành Contrabass không?"**

**CÂU TRẢ LỜI LÀ: KHÔNG! DÙ BẠN CÓ TĂNG LÊN 100 CHIỀU ĐI NỮA CŨNG KHÔNG GIẢI QUYẾT ĐƯỢC LỖI NÀY.**

### 1. Tại sao Bản nhạc Cello nhiều nốt lại ra Contrabass?
Hãy tưởng tượng bạn lấy ảnh chụp cận mặt của 3 người khác nhau, sau đó mang 3 bức ảnh đó **"trộn đè lên nhau" (Lấy Trung bình - Mean)** để tạo ra một khuôn mặt mới. Khuôn mặt tạo ra cuối cùng sẽ không giống ai trong 3 người kia cả, nó mờ ảo và kỳ dị.

Trường hợp File âm thanh của bạn cũng y hệt:
- Hệ thống của chúng ta sử dụng kiến trúc **Global Statistics (Lấy Trung Bình trên toàn bộ thời lượng âm thanh)**. Kiến trúc này được mệnh danh là "Chuẩn mực" để tạo ra DNA cho **NỐT ĐƠN (Single-Note)**.
- Khi bạn ném một **Bản Nhạc Cello** (nhiều nốt cao thấp, nhanh chậm xen kẽ), hệ thống sẽ làm việc một cách mù quáng: Nó cộng dồn sóng âm của nốt C êm ái, với nốt D gắt gỏng, và nốt F trầm hùng... rồi CHIA TRUNG BÌNH.
- Kết cục: Sóng âm bị "cào bằng" lại, tạo ra một **"Bóng Ma Tần Số Thấp"** nặng nề và u ám.
- Khi chui vào Database để tìm kiếm độ giống nhau (Cosine Similarity), bóng ma nặng nề kia hoàn toàn Khớp Lệnh với bản chất ồm ồm, khổng lồ của một nốt **Contrabass**. 
$\rightarrow$ Lỗi không nằm ở số chiều Vector ít hay nhiều, lỗi là do **Thuật toán lấy Trung Bình (Mean Pooling) sẽ phá hủy cấu trúc Giai Điệu Dài.** Để xử lý giai điệu, phải dùng các thuật toán giữ lại trục thời gian (như CNN quét ảnh phổ Spectrogram hoặc LSTM/Transformer).

### 2. Vậy Giai Đoạn 2 (Tăng từ 37 chiều lên 56 chiều) có tác dụng gì?
Nếu V2 không giải quyết được việc nhận diện Bản Nhạc nhiều nốt, vậy tại sao chúng ta lại mất công thêm thắt 19 chiều (RMS Mean, Silence Ratio, Delta MFCC Std, Spectral Bandwidth...) vào làm gì? 

Mục đích thực sự của V2 là **TRANG BỊ "KÍNH HIỂN VI" ĐỂ PHÂN BIỆT NHỮNG NHẠC CỤ HOẶC KỸ THUẬT SIÊU GIỐNG NHAU.**

Ở cấp độ nốt đơn (Đúng với Data TinySOL đang dùng):
* **Phân biệt Kĩ thuật (Technique):** Đàn Violin cùng một nốt C4, người ta kéo vĩ (Arco) và dùng tay gảy (Pizzicato) thì MFCC 37 chiều ở V1 đôi khi bị nhầm lẫn. Nhờ có `Decay Time` và `Silence Ratio` ở V2, hệ thống ngay lập tức nhận ra Pizzicato là kỹ thuật "chết yểu" cực nhanh, còn Arco thì tiếng ngân dài dẳng dẳng.
* **Phân biệt tính "Bẩn" trong âm thanh:** Nốt C4 của Violin nghe rất chói, Nốt C4 của Viola thì ấm hơn (vì hộp đàn to hơn). `Spectral Bandwidth` và `Spectral Flatness` ở V2 đóng vai trò chia tách độ "sắc nhọn" của sóng âm, giúp cỗ máy cảm nhận được sự "Gai góc" khác nhau của 2 loại đàn dù chúng đánh ra cùng một tần số nốt nhạc.
* **Lưu giữ vết tích Rung tay:** 13 chiều `Delta MFCC Std` sinh ra không phải để đo âm lượng, mà là đo "Gia Tốc" biển đổi của âm thanh (Độ rung của tay nhạc công - Vibrato). V1 không phát hiện ra Vibrato tốt như V2.

> **TÓM CHỐT KHÍT CHO BUỔI BẢO VỆ:** 
> V1 (37 chiều) là Lăng kính nhìn **Hình thể** đàn (To hay nhỏ). 
> V2 (56 chiều) là Kính hiển vi nhìn **Cảm xúc và Kỹ năng** tay của nghệ sĩ (Rung, Gảy nhẹ, Cọ nhám dây). Cả hai cơ chế này CẤM CHỈ ĐỊNH ném cả 1 giai điệu bài hát vào, vì thao tác Trộn Trung Bình (Bag of Features Mean) sẽ nghiền nát tất cả các Cảm Xúc đó thành một màu Bass xám ngoét của Contrabass!
