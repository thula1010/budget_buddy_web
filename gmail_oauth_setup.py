"""Authorize Budget Buddy once and print the Gmail OAuth refresh token."""

import os

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow


load_dotenv()
client_id = os.environ.get("GMAIL_CLIENT_ID")
client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
if not client_id or not client_secret:
    raise SystemExit("Hãy đặt GMAIL_CLIENT_ID và GMAIL_CLIENT_SECRET trong file .env trước.")

client_config = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}
flow = InstalledAppFlow.from_client_config(
    client_config, scopes=["https://www.googleapis.com/auth/gmail.send"]
)
credentials = flow.run_local_server(
    host="localhost",
    port=0,
    access_type="offline",
    prompt="consent",
    open_browser=True,
    authorization_prompt_message="Đang mở trình duyệt để bạn cho phép Budget Buddy gửi Gmail...",
    success_message="Đã cấp quyền. Bạn có thể đóng cửa sổ này và quay lại PowerShell.",
)
if not credentials.refresh_token:
    raise SystemExit("Google không trả về Refresh Token. Hãy thu hồi quyền ứng dụng và thử lại.")

print("\nSao chép dòng sau vào Render Environment; không gửi cho người khác:")
print(f"GMAIL_REFRESH_TOKEN={credentials.refresh_token}")
