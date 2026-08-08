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
- Xác minh email bắt buộc khi tạo tài khoản, liên kết hết hạn sau 24 giờ.
- Gửi cảnh báo đúng thời điểm danh mục vừa vượt ngân sách và báo cáo chi tiêu hàng tuần.
- Người dùng tự bật/tắt email hoặc xóa vĩnh viễn tài khoản trong trang Cài đặt.

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

## Email xác minh và thông báo

Khi triển khai trên Render, dùng Resend qua HTTPS. Khai báo các biến sau trong **Environment**:

```dotenv
APP_BASE_URL=https://ten-ung-dung.onrender.com
APP_TIMEZONE=Asia/Ho_Chi_Minh
EMAIL_VERIFICATION_REQUIRED=1
RESEND_API_KEY=re_xxxxxxxxx
EMAIL_FROM=Budget Buddy <notifications@ten-mien-da-xac-minh.com>
```

`EMAIL_FROM` phải thuộc tên miền đã xác minh trên Resend. Khi chạy ở máy chủ khác có hỗ trợ SMTP, có thể thay bằng `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` và `SMTP_USE_TLS` như trong `.env.example`.

Để gửi báo cáo tuần trên Render, tạo **Cron Job** dùng cùng repository và các biến môi trường với Web Service:

Web Service và Cron Job bắt buộc dùng cùng biến `DATABASE_URL` trỏ tới một PostgreSQL dùng chung. Không dùng SQLite mặc định cho bản triển khai này vì hai dịch vụ không chia sẻ cùng tệp database.

```text
Build Command: pip install -r requirements.txt
Command: flask --app app send-weekly-reports
Schedule: 0 1 * * MON
```

Lịch trên chạy lúc 01:00 UTC mỗi thứ Hai, tức 08:00 tại Việt Nam. Lệnh chỉ gửi cho tài khoản đã xác minh, đang bật báo cáo tuần, và không gửi lặp lại cùng một tuần.

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
| `APP_BASE_URL` | `http://127.0.0.1:5000` | Tên miền đầy đủ dùng trong liên kết email |
| `APP_TIMEZONE` | `Asia/Ho_Chi_Minh` | Múi giờ xác định tuần báo cáo |
| `EMAIL_VERIFICATION_REQUIRED` | `1` | Bắt buộc xác minh email khi đăng ký |
| `RESEND_API_KEY` | trống | API key gửi email qua HTTPS |
| `EMAIL_FROM` | trống | Tên và địa chỉ người gửi đã xác minh |
