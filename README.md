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

## Email xác minh và thông báo bằng Gmail API

Gmail API gửi qua HTTPS nên hoạt động trên Render Free. Ứng dụng chỉ yêu cầu quyền `gmail.send` và tự đổi Refresh Token lấy Access Token ngắn hạn trước mỗi lần gửi.

Thiết lập một lần:

1. Tạo project trong [Google Cloud Console](https://console.cloud.google.com/) và bật **Gmail API**.
2. Trong **Google Auth Platform**, cấu hình Branding/Audience và thêm Gmail gửi thư làm Test user.
3. Tạo OAuth Client có loại **Desktop app**, rồi sao chép Client ID và Client Secret.
4. Trên máy tính, đặt hai giá trị vào file `.env`:

```dotenv
GMAIL_CLIENT_ID=xxxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=xxxx
```

5. Cài dependency và chạy công cụ cấp quyền:

```powershell
pip install -r requirements.txt
python gmail_oauth_setup.py
```

6. Đăng nhập đúng Gmail gửi thư, chấp nhận quyền gửi mail, rồi sao chép dòng `GMAIL_REFRESH_TOKEN=...` được in trong PowerShell.
7. Trong Render **Environment**, khai báo:

```dotenv
APP_BASE_URL=https://ten-ung-dung.onrender.com
APP_TIMEZONE=Asia/Ho_Chi_Minh
EMAIL_VERIFICATION_REQUIRED=1
EMAIL_USER=your-gmail@gmail.com
EMAIL_FROM="Budget Buddy <your-gmail@gmail.com>"
GMAIL_CLIENT_ID=xxxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=xxxx
GMAIL_REFRESH_TOKEN=xxxx
```

Không đưa Client Secret hoặc Refresh Token lên GitHub. Gmail API được ưu tiên khi có đủ bốn biến `GMAIL_*`/`EMAIL_USER`; Resend và SMTP chỉ còn là fallback tương thích. Nếu OAuth Audience đang ở trạng thái **Testing**, quyền và Refresh Token của test user sẽ hết hạn sau 7 ngày; chuyển Publishing status sang **Production** để tránh giới hạn này cho cấu hình lâu dài.

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
| `EMAIL_USER` | trống | Tài khoản Gmail gửi thông báo |
| `EMAIL_FROM` | trống | Tên hiển thị và địa chỉ Gmail gửi |
| `GMAIL_CLIENT_ID` | trống | OAuth Client ID của Google Cloud |
| `GMAIL_CLIENT_SECRET` | trống | OAuth Client Secret, chỉ đặt trong Environment |
| `GMAIL_REFRESH_TOKEN` | trống | Token cấp quyền gửi Gmail khi người dùng offline |
