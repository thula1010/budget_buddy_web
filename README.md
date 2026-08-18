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
- Chuyển đổi ngôn ngữ (Tiếng Việt / English) và đơn vị tiền (VND, USD, EUR, JPY) ngay trên thanh trên cùng của mọi trang.
- AI Coach lưu lịch sử trò chuyện theo từng cuộc, mở lại/đổi tên/xóa bất cứ lúc nào.
- Tự thêm, sửa và xóa tài khoản tiền (ngân hàng, ví điện tử, tiền mặt, thẻ tín dụng, tiết kiệm, đầu tư).

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

## Ngôn ngữ và đơn vị tiền

Widget ở góc trên bên phải mỗi trang cho phép đổi ngôn ngữ và đơn vị tiền ngay lập tức; trang **Cài đặt** có phiên bản đầy đủ với tên tiền tệ. Lựa chọn được lưu vào tài khoản (`user.language`, `user.currency`) nên theo bạn sang thiết bị khác, đồng thời lưu vào `localStorage` để trang hiển thị đúng ngay từ lần vẽ đầu tiên.

Mọi số tiền **luôn được lưu trong database bằng VND**. Đổi đơn vị tiền chỉ đổi cách hiển thị và cách đọc số bạn nhập vào form, không ghi lại dữ liệu cũ — nhờ vậy sổ sách không bao giờ lệch. Khi bạn nhập `10` lúc đang chọn USD, ứng dụng lưu `254000` VND.

Tỷ giá là hằng số trong mã nguồn, khai báo ở hai nơi phải khớp nhau:

| Nơi khai báo | Dùng cho |
|---|---|
| `CURRENCY_RATES` trong [`app.py`](app.py) | Câu trả lời của AI Coach và email |
| `CURRENCIES` trong [`static/js/bb-i18n.js`](static/js/bb-i18n.js) | Toàn bộ giao diện |

Muốn đổi tỷ giá hoặc thêm một đơn vị tiền mới, sửa cả hai danh sách trên. Giá trị `rate` là "một đơn vị tiền đó bằng bao nhiêu VND".

Chuỗi giao diện nằm trong từ điển `DICT` của `bb-i18n.js`. Thẻ HTML tĩnh dịch bằng thuộc tính `data-i18n="khóa"`; phần dựng bằng JavaScript gọi `BB.t('khóa')`. Thông báo lỗi từ server dịch qua bảng `UI_MESSAGES` trong `app.py`.

## Lịch sử trò chuyện AI Coach

Mỗi câu hỏi và câu trả lời được lưu vào hai bảng `chat_session` và `chat_message`, tách theo người dùng. Trang AI Coach có cột lịch sử bên trái để:

- mở lại một cuộc trò chuyện cũ cùng toàn bộ tin nhắn;
- bắt đầu cuộc trò chuyện mới (tiêu đề tự đặt theo câu hỏi đầu tiên);
- đổi tên hoặc xóa từng cuộc, hoặc xóa sạch lịch sử.

Khi có `OPENAI_API_KEY`, 12 tin nhắn gần nhất của cuộc trò chuyện được gửi kèm để AI hiểu ngữ cảnh câu hỏi tiếp theo. Mỗi tài khoản giữ tối đa 100 cuộc trò chuyện gần nhất; cuộc cũ hơn tự động được dọn. Xóa tài khoản sẽ xóa luôn toàn bộ lịch sử.

## Quản lý tài khoản tiền

Trong thẻ **Danh sách tài khoản** ở trang Tổng quan, mỗi tài khoản có ba nút: *Chỉnh số dư*, *Sửa* và *Xóa*; cuối danh sách là nút **+ Thêm tài khoản**.

Sáu loại tài khoản được hỗ trợ: `cash`, `bank`, `ewallet`, `credit`, `savings`, `investment` (khai báo trong `ACCOUNT_TYPES` của `app.py`). Tên tài khoản không được trùng nhau trong cùng một người dùng, và mỗi người tối đa 30 tài khoản.

Khi xóa một tài khoản còn giao dịch, ứng dụng bắt buộc chọn một tài khoản khác để nhận lịch sử. Số dư ban đầu cũng được cộng sang tài khoản đó nên **tổng số dư không đổi**. Mục tiêu đang liên kết sẽ trỏ sang tài khoản mới. Không thể xóa tài khoản cuối cùng.

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

## Triển khai lên Render

Cách nhanh nhất: push repo này lên GitHub, vào Render Dashboard chọn **New +** → **Blueprint**, trỏ tới repo — Render sẽ đọc sẵn [`render.yaml`](render.yaml) và tự tạo Web Service + Cron Job + PostgreSQL dùng chung. Sau khi tạo xong, vào tab **Environment** của từng service để điền các biến đánh dấu "sync: false" trong file (API key, Gmail OAuth, `APP_BASE_URL` là domain `.onrender.com` thật của bạn...).

Nếu tạo thủ công qua dashboard thay vì Blueprint, cấu hình như sau:

**Web Service:**
```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn --bind 0.0.0.0:$PORT app:app
```

**Cron Job** (báo cáo tuần), dùng cùng repository và các biến môi trường với Web Service:

```text
Build Command: pip install -r requirements.txt
Command: flask --app app send-weekly-reports
Schedule: 0 1 * * MON
```

Lịch trên chạy lúc 01:00 UTC mỗi thứ Hai, tức 08:00 tại Việt Nam. Lệnh chỉ gửi cho tài khoản đã xác minh, đang bật báo cáo tuần, và không gửi lặp lại cùng một tuần.

Web Service và Cron Job bắt buộc dùng cùng biến `DATABASE_URL` trỏ tới một PostgreSQL dùng chung. Không dùng SQLite mặc định cho bản triển khai này vì hai dịch vụ không chia sẻ cùng tệp database. Render cấp `DATABASE_URL` dạng `postgres://`; ứng dụng đã tự chuyển thành `postgresql://` để tương thích SQLAlchemy, không cần chỉnh tay.

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
- chuyển đổi database phiên bản cũ;
- lưu/từ chối tùy chọn ngôn ngữ và tiền tệ, và việc số tiền vẫn nằm nguyên bằng VND;
- tạo, đổi tên, xóa cuộc trò chuyện và tính riêng tư của lịch sử chat;
- thêm/sửa/xóa tài khoản tiền, chuyển giao dịch khi xóa và bảo toàn tổng số dư.

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
