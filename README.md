# Budget Buddy

Ứng dụng quản lý tài chính cá nhân bằng Flask, SQLite và AI.

## Tính năng

- Giao dịch được lưu bền vững trong SQLite và hiển thị ngay trong lịch sử.
- Số dư Overview, Transactions, Budgets và AI Coach dùng chung một nguồn dữ liệu.
- Dữ liệu tài khoản, giao dịch, ngân sách và mục tiêu được tách theo người dùng.
- Xóa giao dịch tự động hoàn tác ảnh hưởng lên số dư và ngân sách.
- AI Coach phân tích số dư, chi tiêu, ngân sách và mục tiêu thực tế của người dùng.
- Chụp hoặc tải ảnh hóa đơn trên điện thoại; AI tự điền cửa hàng, tổng tiền, ngày và danh mục.
- Tự động nâng cấp database từ cấu trúc cũ mà không làm mất giao dịch/mục tiêu.

## Cài đặt

Yêu cầu Python 3.10 trở lên.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Trên macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Mở `http://127.0.0.1:5000` và tạo tài khoản.

## Bật AI Coach và OCR hóa đơn

Điền API key vào `.env`:

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.6-luna
```

Không có API key, ứng dụng vẫn hoạt động đầy đủ với bộ gợi ý tài chính cục bộ. Riêng OCR sẽ báo chưa cấu hình thay vì tạo dữ liệu hóa đơn giả.

Ảnh OCR hỗ trợ JPG, PNG và WebP, tối đa 8 MB. Trên điện thoại, nút chọn ảnh có thể mở camera sau.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

Bộ kiểm thử bao phủ:

- thêm, tải lại và xóa giao dịch;
- đồng bộ số dư/ngân sách;
- cách ly dữ liệu giữa người dùng;
- kiểm tra số dư không đủ;
- AI fallback và lỗi cấu hình OCR;
- chuyển đổi database phiên bản cũ.

## Cấu hình

| Biến | Mặc định | Mục đích |
|---|---|---|
| `SECRET_KEY` | giá trị chỉ dành cho phát triển | Khóa phiên đăng nhập; bắt buộc đổi khi triển khai |
| `DATABASE_URL` | `sqlite:///instance/app.db` | Kết nối database |
| `OPENAI_API_KEY` | trống | Bật AI Coach nâng cao và OCR |
| `OPENAI_MODEL` | `gpt-5.6-luna` | Model dùng cho AI/OCR |
| `FLASK_DEBUG` | `0` | Đặt `1` chỉ khi phát triển |
