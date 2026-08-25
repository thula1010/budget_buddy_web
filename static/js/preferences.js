(function () {
  'use strict';

  const config = window.BB_PREFERENCES || {};
  const language = config.language === 'vi' ? 'vi' : 'en';
  const currency = config.currency === 'USD' ? 'USD' : 'VND';
  const usdVndRate = Number(config.usd_vnd_rate) > 0 ? Number(config.usd_vnd_rate) : 25000;

  const pairs = [
    ['Overview', 'Tổng quan'], ['Transactions', 'Giao dịch'], ['Budgets', 'Ngân sách'],
    ['Goals', 'Mục tiêu'], ['AI Coach', 'Trợ lý AI'], ['Settings', 'Cài đặt'],
    ['Logout', 'Đăng xuất'], ['Cancel', 'Hủy'], ['Save', 'Lưu'], ['Close', 'Đóng'],
    ['Edit', 'Sửa'], ['Delete', 'Xóa'], ['Review', 'Xem lại'], ['Active', 'Đang hoạt động'],
    ['All accounts synced', 'Tất cả tài khoản đã đồng bộ'],
    ['Across all accounts', 'Trên tất cả tài khoản'], ['Accounts Overview', 'Tổng quan tài khoản'],
    ['Total across accounts', 'Tổng số dư các tài khoản'], ['Link Account', 'Liên kết tài khoản'],
    ['Balance', 'Số dư'], ['Income', 'Thu nhập'], ['Spending', 'Chi tiêu'],
    ['Savings Rate', 'Tỷ lệ tiết kiệm'], ['Target', 'Mục tiêu'], ['This month', 'Tháng này'],
    ['Cash', 'Tiền mặt'], ['Bank Accounts', 'Tài khoản ngân hàng'], ['E-wallets', 'Ví điện tử'],
    ['Add Transaction', 'Thêm giao dịch'], ['Edit Transaction', 'Sửa giao dịch'],
    ['Expense', 'Khoản chi'], ['Date', 'Ngày'], ['Description', 'Nội dung'],
    ['Amount', 'Số tiền'], ['Category', 'Danh mục'], ['Account', 'Tài khoản'],
    ['Merchant / Description', 'Cửa hàng / Nội dung'], ['Select account', 'Chọn tài khoản'],
    ['Select category', 'Chọn danh mục'], ['Save Transaction', 'Lưu giao dịch'],
    ['Recent Transactions', 'Giao dịch gần đây'], ['All Transactions', 'Tất cả giao dịch'],
    ['Search transactions...', 'Tìm giao dịch...'], ['Export CSV', 'Xuất CSV'],
    ['Upload Receipt', 'Tải hóa đơn'], ['Choose receipt image', 'Chọn ảnh hóa đơn'],
    ['AI will fill in the transaction details.', 'AI sẽ tự điền thông tin giao dịch.'],
    ['Total Budget', 'Tổng ngân sách'], ['Spent', 'Đã chi'], ['Remaining', 'Còn lại'],
    ['Over Budget', 'Vượt ngân sách'], ['Budget Limit Exceeded Alert', 'Cảnh báo vượt ngân sách'],
    ['Edit Budget Limit', 'Sửa hạn mức ngân sách'], ['Budget limit', 'Hạn mức ngân sách'],
    ['Save limit', 'Lưu hạn mức'], ['Review budget', 'Xem ngân sách'],
    ['Budget Status', 'Trạng thái ngân sách'], ['Monthly Spending', 'Chi tiêu theo tháng'],
    ['Create Goal', 'Tạo mục tiêu'], ['New Goal', 'Mục tiêu mới'], ['Goal name', 'Tên mục tiêu'],
    ['Target amount', 'Số tiền mục tiêu'], ['Already saved', 'Đã tích lũy'],
    ['Deadline', 'Thời hạn'], ['Deposit Funds', 'Nạp vào mục tiêu'],
    ['Amount to Deposit', 'Số tiền cần nạp'], ['Confirm Deposit', 'Xác nhận nạp'],
    ['Progress', 'Tiến độ'], ['Saved', 'Đã tích lũy'], ['Completed', 'Đã hoàn thành'],
    ['Notifications', 'Thông báo'], ['Quick questions', 'Câu hỏi nhanh'],
    ['Ask Budget Buddy...', 'Hỏi Budget Buddy...'], ['Send', 'Gửi'],
    ['Food & Drinks', 'Ăn uống'], ['Transport', 'Di chuyển'], ['Education', 'Giáo dục'],
    ['Entertainment', 'Giải trí'], ['Shopping', 'Mua sắm'], ['Other', 'Khác'],
    ['Language & currency', 'Ngôn ngữ & tiền tệ'], ['Language', 'Ngôn ngữ'],
    ['Display currency', 'Tiền tệ hiển thị'], ['English', 'Tiếng Anh'], ['Vietnamese', 'Tiếng Việt'],
    ['Email notifications', 'Thông báo email'], ['Weekly spending report', 'Báo cáo chi tiêu hàng tuần'],
    ['Budget limit alerts', 'Cảnh báo vượt ngân sách'], ['Save preferences', 'Lưu tùy chọn'],
    ['Account information', 'Thông tin tài khoản'], ['Email status', 'Trạng thái email'],
    ['Verified', 'Đã xác minh'], ['Not verified', 'Chưa xác minh'],
    ['Danger zone', 'Khu vực nguy hiểm'], ['Delete account permanently', 'Xóa tài khoản vĩnh viễn'],
    ['Delete account', 'Xóa tài khoản'], ['Current password', 'Mật khẩu hiện tại'],
    ['Type DELETE to confirm', 'Nhập DELETE để xác nhận'],
    ['Preferences saved.', 'Đã lưu tùy chọn.'], ['Unable to save preferences.', 'Không thể lưu tùy chọn.'],
    ['Cancel', 'Hủy'], ['No transactions yet.', 'Chưa có giao dịch.'],
    ['No goals yet.', 'Chưa có mục tiêu.'], ['No spending data yet.', 'Chưa có dữ liệu chi tiêu.'],
    ['Account settings', 'Cài đặt tài khoản'],
    ['Manage email notifications and your personal data.', 'Quản lý email thông báo và dữ liệu cá nhân của bạn.'],
    ['Username', 'Tên đăng nhập'],
    ['Receive an income and spending summary, a comparison with last week, and your largest spending categories.', 'Nhận tổng hợp thu, chi, so sánh tuần trước và các nhóm chi tiêu lớn.'],
    ['Send one email when a category first crosses its monthly limit.', 'Gửi email một lần khi một danh mục vừa vượt hạn mức trong tháng.'],
    ['Delete your account and all accounts, transactions, budgets, and goals permanently. This data cannot be recovered.', 'Xóa vĩnh viễn tài khoản cùng toàn bộ tài khoản tiền, giao dịch, ngân sách và mục tiêu của bạn. Dữ liệu không thể khôi phục.'],
    ['Confirm account deletion', 'Xác nhận xóa tài khoản'],
    ['Enter your password and the word DELETE. This action cannot be undone.', 'Nhập mật khẩu và chữ DELETE. Hành động này không thể hoàn tác.'],
    ['Password', 'Mật khẩu'], ['Enter DELETE', 'Nhập DELETE'], ['Delete permanently', 'Xóa vĩnh viễn'],
    ['Attached receipt', 'Hóa đơn đính kèm (Receipt)'],
    ['Drag and drop or click to upload a receipt', 'Kéo thả hoặc click để tải hóa đơn'],
    ['Automatically extract details with AI (JPG, PNG)', 'Tự động nhận diện thông tin bằng AI (JPG, PNG)'],
    ['Merchant / Description', 'Merchant / Mô tả'], ['e.g. Highlands Coffee', 'VD: Highlands Coffee'],
    ['Paid via / Account', 'Thanh toán bằng / Tài khoản'], ['Delete image', 'Xóa ảnh'],
    ['Edit account balance', 'Chỉnh số dư tài khoản'],
    ['Transaction history is preserved. The new balance is synchronized throughout the app.', 'Lịch sử giao dịch được giữ nguyên. Số dư mới sẽ đồng bộ trên toàn ứng dụng.'],
    ['Save balance', 'Lưu số dư'], ['Edit budget limit', 'Chỉnh hạn mức ngân sách'],
    ['Save limit', 'Lưu hạn mức'], ['Email alert sent!', 'Đã gửi email cảnh báo!'],
    ['You have exceeded your category limit.', 'Bạn đã vượt hạn mức danh mục.'], ['Acknowledge', 'Đã hiểu'],
    ['Track your saving milestones', 'Theo dõi các cột mốc tiết kiệm'],
    ['Add New Goal', 'Thêm mục tiêu mới'], ['Goal Name', 'Tên mục tiêu'],
    ['Initial Saved', 'Số tiền ban đầu'], ['Accent Color', 'Màu nhấn'], ['Icon Emoji', 'Biểu tượng'],
    ['Linked account (deposits are deducted here)', 'Tài khoản riêng (tiền nạp sẽ trừ từ đây)'],
    ['No linked account', 'Không liên kết tài khoản'], ['Save Goal', 'Lưu mục tiêu'],
    ['Enter a negative amount (for example, -100000) to undo part of a mistaken deposit.', 'Nhập số âm (VD: -100000) nếu lỡ nạp nhầm và muốn rút bớt.'],
    ['No matching transactions.', 'Chưa có giao dịch nào phù hợp.'],
    ['All categories', 'Tất cả danh mục'], ['From date', 'Từ ngày'], ['To date', 'Đến ngày'],
    ['Please enter a transaction name.', 'Vui lòng nhập tên giao dịch.'],
    ['Amount must be greater than 0.', 'Số tiền phải lớn hơn 0.'],
    ['The category or account is missing.', 'Thiếu danh mục hoặc tài khoản.'],
    ['Transaction not found.', 'Không tìm thấy giao dịch.'], ['Error', 'Lỗi'],
    ['Please select a receipt image.', 'Vui lòng chọn file hình ảnh hóa đơn.'],
    ['Scanning receipt...', 'Đang quét dữ liệu hóa đơn...'],
    ['Unable to read the receipt.', 'Không thể đọc hóa đơn.'],
    ['No OCR data was returned.', 'Không nhận được dữ liệu OCR.'],
    ['Receipt details extracted.', 'Đã trích xuất xong từ hóa đơn!'],
    ['Reading receipt with AI...', 'Đang đọc hóa đơn bằng AI...'],
    ['Receipt details filled in. Please review them before saving.', 'Đã điền thông tin từ hóa đơn. Vui lòng kiểm tra trước khi lưu.'],
    ['Unable to update the balance.', 'Không thể cập nhật số dư.'],
    ['Edit funding source', 'Chỉnh sửa nguồn tiền'], ['Funding source name', 'Tên nguồn tiền'],
    ['Current balance', 'Số dư hiện tại'],
    ['Save changes', 'Lưu thay đổi'], ['Delete funding source', 'Xóa nguồn tiền'],
    ['Transaction history is preserved when you change the name or balance. Updates are synchronized throughout the app.', 'Lịch sử giao dịch được giữ nguyên khi đổi tên hoặc số dư. Thay đổi sẽ đồng bộ trên toàn ứng dụng.'],
    ['Transactions linked to this source will also be permanently deleted.', 'Các giao dịch gắn với nguồn tiền này cũng sẽ bị xóa vĩnh viễn.'],
    ['Funding source name is required.', 'Vui lòng nhập tên nguồn tiền.'],
    ['Unable to update the funding source.', 'Không thể cập nhật nguồn tiền.'],
    ['Unable to delete the funding source.', 'Không thể xóa nguồn tiền.'],
    ['Link funding source', 'Liên kết nguồn tiền'], ['Funding source type', 'Loại nguồn tiền'],
    ['Bank account', 'Tài khoản ngân hàng'], ['E-wallet', 'Ví điện tử'],
    ['Bank / funding source name', 'Tên ngân hàng / nguồn tiền'],
    ['e.g. Vietcombank', 'VD: Vietcombank'], ['Create funding source', 'Tạo nguồn tiền'],
    ['Enter the current available balance. It will become the starting balance for this source.', 'Nhập số dư hiện có. Đây sẽ là số dư ban đầu của nguồn tiền này.'],
    ['Unable to create the funding source.', 'Không thể tạo nguồn tiền.'],
    ['Unable to update the budget limit.', 'Không thể cập nhật hạn mức.'],
    ['Unable to save the transaction.', 'Không thể lưu giao dịch'],
    ['Unable to delete the account.', 'Không thể xóa tài khoản.']
    ,['Log in', 'Đăng nhập'], ['Sign up', 'Đăng ký'], ['Enter username', 'Nhập username'],
    ['Confirm password', 'Nhập lại mật khẩu'], ['Create account', 'Tạo tài khoản'],
    ['Check your inbox', 'Kiểm tra hộp thư của bạn'],
    ['We sent a verification link to', 'Chúng tôi đã gửi liên kết xác minh tới'],
    ['The link is valid for 24 hours.', 'Liên kết có hiệu lực trong 24 giờ.'],
    ['Did not receive the email?', 'Chưa nhận được email?'],
    ['Resend verification email', 'Gửi lại email xác minh'], ['Back to login', 'Quay lại đăng nhập'],
    ['Edit', 'Chỉnh sửa'], ['No transactions yet.', 'Chưa có giao dịch nào.']
    ,['✓ Verified', '✓ Đã xác minh'],
    ['Amounts are stored safely in VND. USD display uses the configured conversion rate.', 'Dữ liệu tiền được lưu an toàn bằng VND. Chế độ USD dùng tỷ giá đã cấu hình.']
    ,['Synced', 'Đã đồng bộ'], ['+ Add Transaction', '+ Thêm giao dịch'],
    ['Scholarship + tutoring', 'Học bổng + dạy thêm'],
    ['Spending by Category', 'Chi tiêu theo danh mục'], ['Weekly Spend', 'Chi tiêu theo tuần'],
    ['💵 CASH', '💵 TIỀN MẶT'], ['🏦 BANK ACCOUNTS', '🏦 TÀI KHOẢN NGÂN HÀNG'],
    ['📱 E-WALLETS', '📱 VÍ ĐIỆN TỬ'], ['bank', 'ngân hàng'], ['ewallet', 'ví điện tử'],
    ['● Active', '● Đang hoạt động'], ['+ Link Account', '+ Liên kết tài khoản']
    ,['Total Spent', 'Tổng đã chi'], ['AI Insight', 'Gợi ý AI'],
    ['No significant spending recorded yet this month.', 'Tháng này chưa có khoản chi đáng kể.']
    ,['Total Income', 'Tổng thu nhập'], ['Total Expenses', 'Tổng chi tiêu'],
    ['Net This Month', 'Ròng tháng này'], ['Merchant', 'Nội dung'],
    ['+ New Goal', '+ Mục tiêu mới'], ['Total Saved Across Goals', 'Tổng tiền đã tích lũy'],
    ['Personal Smart Assistant', 'Trợ lý tài chính thông minh'], ['Send ↑', 'Gửi ↑'],
    ['New chat', 'Chat mới'], ['Close chat', 'Đóng trò chuyện'],
    ['Quick Prompts', 'Gợi ý nhanh'], ['Of', 'trên'], ['completed', 'hoàn thành']
  ];

  const lookup = new Map();
  pairs.forEach(([en, vi]) => {
    lookup.set(en.toLowerCase(), { en, vi });
    lookup.set(vi.toLowerCase(), { en, vi });
  });

  function text(en, vi) { return language === 'vi' ? vi : en; }
  function category(value) {
    const item = lookup.get(String(value || '').trim().toLowerCase());
    return item ? item[language] : String(value || '');
  }
  function toDisplay(amount) { return currency === 'USD' ? Number(amount) / usdVndRate : Number(amount); }
  function toBase(amount) { return currency === 'USD' ? Number(amount) * usdVndRate : Number(amount); }
  function compactAmount(amount) {
    const value = toDisplay(amount);
    const absolute = Math.abs(value);
    if (absolute >= 1e6) return `${(value / 1e6).toFixed(1).replace('.0', '')}M`;
    if (absolute >= 1e3) return `${(value / 1e3).toFixed(1).replace('.0', '')}K`;
    return currency === 'USD' ? value.toFixed(2).replace(/\.00$/, '') : Math.round(value).toLocaleString(language === 'vi' ? 'vi-VN' : 'en-US');
  }
  function formatMoney(amount, options) {
    options = options || {};
    const value = toDisplay(amount);
    if (options.compact) {
      const compact = compactAmount(amount);
      if (options.symbol === false) return compact;
      if (currency === 'USD') return compact.startsWith('-') ? `-$${compact.slice(1)}` : `$${compact}`;
      return `${compact} ₫`;
    }
    const formatted = new Intl.NumberFormat(language === 'vi' ? 'vi-VN' : 'en-US', {
      minimumFractionDigits: currency === 'USD' ? 2 : 0,
      maximumFractionDigits: currency === 'USD' ? 2 : 0
    }).format(Math.abs(value));
    const sign = value < 0 ? '-' : '';
    return currency === 'USD' ? `${sign}$${formatted}` : `${sign}${formatted} ₫`;
  }
  function inputValue(amount) {
    const value = toDisplay(amount);
    return currency === 'USD' ? value.toFixed(2) : String(Math.round(value));
  }
  function currencyLabel() { return currency; }

  function translateValue(value) {
    const trimmed = String(value || '').trim();
    const item = lookup.get(trimmed.toLowerCase());
    if (item) return item[language];
    if (language === 'vi' && /^Target \d+%$/i.test(trimmed)) return trimmed.replace(/^Target/i, 'Mục tiêu');
    if (language === 'en' && /^Tháng \d+$/i.test(trimmed)) return trimmed.replace(/^Tháng/i, 'Month');
    return value;
  }
  function translateTree(root) {
    if (!root) return;
    if (root.nodeType === Node.TEXT_NODE) {
      const original = root.nodeValue;
      const trimmed = original.trim();
      const translated = translateValue(trimmed);
      if (translated !== trimmed) root.nodeValue = original.replace(trimmed, translated);
      return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
    const translateAttributes = element => {
      ['placeholder', 'title', 'aria-label'].forEach(attr => {
        if (element.hasAttribute(attr)) element.setAttribute(attr, translateValue(element.getAttribute(attr)));
      });
      if (element.matches('[data-currency-label]')) element.textContent = currencyLabel();
    };
    if (root.nodeType === Node.ELEMENT_NODE) translateAttributes(root);
    if (root.querySelectorAll) root.querySelectorAll('*').forEach(translateAttributes);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) translateTree(node);
  }

  window.BB = {
    language, currency, usdVndRate, text, category, toDisplay, toBase,
    compactAmount, formatMoney, inputValue, currencyLabel, translateTree
  };
  document.documentElement.lang = language;
  document.addEventListener('DOMContentLoaded', function () {
    translateTree(document.body);
    const observer = new MutationObserver(records => records.forEach(record => {
      record.addedNodes.forEach(translateTree);
    }));
    observer.observe(document.body, { childList: true, subtree: true });
  });
})();
