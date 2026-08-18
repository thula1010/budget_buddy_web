/*
 * Budget Buddy — shared language + currency layer.
 *
 * Every amount in the database is stored in VND. This module only changes how
 * numbers are rendered and how user input is read back, so switching currency
 * never rewrites the ledger.
 *
 * Usage inside a page script:
 *   BB.t('nav.overview')            -> translated string
 *   BB.money(1450000)               -> short form, e.g. "1.5M ₫" or "$57.09"
 *   BB.full(1450000)                -> full form, e.g. "1.450.000 ₫"
 *   BB.toBase(userInput)            -> converts a typed amount back to VND
 *   BB.fromBase(vnd)                -> converts VND into the display currency
 */
(function (global) {
  'use strict';

  var LANG_KEY = 'bb_language';
  var CUR_KEY = 'bb_currency';

  var LANGUAGES = [
    { code: 'vi', label: 'Tiếng Việt', flag: '🇻🇳' },
    { code: 'en', label: 'English', flag: '🇬🇧' }
  ];

  /* How many VND one unit of each currency is worth. Edit here to update rates. */
  var CURRENCIES = [
    { code: 'VND', symbol: '₫', rate: 1, decimals: 0, position: 'suffix', label: 'Việt Nam Đồng' },
    { code: 'USD', symbol: '$', rate: 25400, decimals: 2, position: 'prefix', label: 'US Dollar' },
    { code: 'EUR', symbol: '€', rate: 27500, decimals: 2, position: 'prefix', label: 'Euro' },
    { code: 'JPY', symbol: '¥', rate: 165, decimals: 0, position: 'prefix', label: 'Japanese Yen' }
  ];

  var DICT = {
    vi: {
      'nav.overview': 'Tổng quan',
      'nav.transactions': 'Giao dịch',
      'nav.budgets': 'Ngân sách',
      'nav.goals': 'Mục tiêu',
      'nav.coach': 'AI Coach',
      'nav.settings': 'Cài đặt',
      'nav.logout': 'Đăng xuất',
      'brand.tagline': '· Tài chính thông minh',
      'common.plan': 'Sinh viên',
      'common.synced': 'Đã đồng bộ',
      'common.save': 'Lưu',
      'common.cancel': 'Hủy',
      'common.delete': 'Xóa',
      'common.edit': 'Sửa',
      'common.close': 'Đóng',
      'common.confirm': 'Xác nhận',
      'common.saving': 'Đang lưu…',
      'common.loading': 'Đang tải…',
      'common.error': 'Đã xảy ra lỗi',
      'common.none': 'Không có',
      'common.language': 'Ngôn ngữ',
      'common.currency': 'Đơn vị tiền',
      'common.rate_note': 'Số liệu luôn lưu bằng VND, chỉ thay đổi cách hiển thị.',

      'page.overview.title': 'Tổng quan',
      'page.overview.sub': 'Tất cả tài khoản đã đồng bộ',
      'page.transactions.title': 'Giao dịch',
      'page.transactions.sub': 'Toàn bộ thu chi của bạn',
      'page.budgets.title': 'Ngân sách',
      'page.budgets.sub': 'Tất cả tài khoản đã đồng bộ',
      'page.goals.title': 'Mục tiêu',
      'page.goals.sub': 'Theo dõi tiến độ tiết kiệm',
      'page.coach.title': 'AI Coach',
      'page.coach.sub': 'Trợ lý tài chính cá nhân',

      'kpi.balance': 'SỐ DƯ',
      'kpi.balance.sub': 'Tất cả tài khoản',
      'kpi.income': 'THU NHẬP',
      'kpi.income.sub': 'Trong tháng này',
      'kpi.spending': 'CHI TIÊU',
      'kpi.spending.sub': '{month}',
      'kpi.savings_rate': 'TỶ LỆ TIẾT KIỆM',
      'kpi.savings_rate.sub': 'Mục tiêu {target}%',
      'kpi.total_income': 'TỔNG THU',
      'kpi.total_expense': 'TỔNG CHI',
      'kpi.net': 'CÒN LẠI THÁNG NÀY',
      'kpi.total_budget': 'TỔNG NGÂN SÁCH',
      'kpi.total_spent': 'ĐÃ CHI',
      'kpi.remaining': 'CÒN LẠI',

      'overview.alert': 'Ngân sách <b>{category}</b> đã vượt — quá <b>{amount}</b>',
      'overview.review': 'Xem lại',
      'accounts.title': 'Danh sách tài khoản',
      'accounts.total': 'Tổng các tài khoản',
      'accounts.add': '+ Thêm tài khoản',
      'accounts.add_title': 'Thêm tài khoản mới',
      'accounts.edit_title': 'Sửa tài khoản',
      'accounts.name': 'Tên tài khoản',
      'accounts.name_hint': 'VD: Vietcombank, ZaloPay, Ví tiền mặt',
      'accounts.type': 'Loại tài khoản',
      'accounts.icon': 'Biểu tượng',
      'accounts.opening_balance': 'Số dư ban đầu',
      'accounts.active': '● Đang hoạt động',
      'accounts.delete_confirm': 'Xóa tài khoản “{name}”?',
      'accounts.delete_with_txn': 'Tài khoản “{name}” còn {count} giao dịch. Chọn tài khoản nhận lịch sử chuyển sang:',
      'accounts.move_to': 'Chuyển giao dịch sang',
      'accounts.deleted': 'Đã xóa tài khoản.',
      'accounts.created': 'Đã thêm tài khoản.',
      'accounts.updated': 'Đã cập nhật tài khoản.',
      'accounts.edit_balance': 'Chỉnh số dư',
      'accounts.balance_title': 'Cập nhật số dư',
      'accounts.balance_hint': 'Toàn bộ lịch sử giao dịch được giữ nguyên; chỉ số dư ban đầu được điều chỉnh.',
      'accounts.current_balance': 'Số dư hiện tại',
      'accounts.min_one': 'Cần giữ lại ít nhất một tài khoản.',
      'accounts.invalid_balance': 'Vui lòng nhập số dư hợp lệ, từ 0 trở lên.',
      'accounts.invalid_name': 'Vui lòng nhập tên tài khoản.',

      'acctype.cash': 'Tiền mặt',
      'acctype.bank': 'Ngân hàng',
      'acctype.ewallet': 'Ví điện tử',
      'acctype.credit': 'Thẻ tín dụng',
      'acctype.savings': 'Tiết kiệm',
      'acctype.investment': 'Đầu tư',
      'acctype.cash.group': '💵 TIỀN MẶT',
      'acctype.bank.group': '🏦 TÀI KHOẢN NGÂN HÀNG',
      'acctype.ewallet.group': '📱 VÍ ĐIỆN TỬ',
      'acctype.credit.group': '💳 THẺ TÍN DỤNG',
      'acctype.savings.group': '🐖 TIẾT KIỆM',
      'acctype.investment.group': '📈 ĐẦU TƯ',

      'txn.add': '+ Thêm giao dịch',
      'txn.add_title': 'Thêm giao dịch',
      'txn.edit_title': 'Sửa giao dịch',
      'txn.expense': 'Chi tiêu',
      'txn.income': 'Thu nhập',
      'txn.merchant': 'Nơi chi / Mô tả',
      'txn.merchant_hint': 'VD: Highlands Coffee',
      'txn.amount': 'Số tiền',
      'txn.date': 'Ngày',
      'txn.category': 'Danh mục',
      'txn.account': 'Trả bằng / Tài khoản',
      'txn.save': 'Lưu giao dịch',
      'txn.save_changes': 'Lưu thay đổi',
      'txn.search': '🔍  Tìm theo nơi chi, danh mục, tài khoản…',
      'txn.export': 'Xuất CSV',
      'txn.empty': 'Chưa có giao dịch nào phù hợp.',
      'txn.recent': 'Giao dịch gần đây',
      'txn.col.merchant': 'Nơi chi',
      'txn.col.category': 'Danh mục',
      'txn.col.account': 'Tài khoản',
      'txn.col.amount': 'Số tiền',
      'txn.delete_confirm': 'Xóa giao dịch này? Số dư tài khoản sẽ được hoàn lại.',
      'txn.ai_tagged': 'AI gán nhãn',
      'txn.balance_after': 'Số dư {account} sau giao dịch:',
      'txn.insufficient': '⚠️ không đủ số dư',
      'txn.all_categories': 'Tất cả danh mục',
      'txn.from_date': 'Từ ngày',
      'txn.to_date': 'Đến ngày',

      'receipt.label': 'Hóa đơn đính kèm',
      'receipt.drop': 'Kéo thả hoặc bấm để tải hóa đơn',
      'receipt.hint': 'Tự động nhận diện thông tin bằng AI (JPG, PNG)',
      'receipt.scanning': 'Đang quét dữ liệu hóa đơn…',
      'receipt.done': 'Đã trích xuất xong từ hóa đơn!',
      'receipt.failed': 'Lỗi khi đọc hóa đơn: {error}',
      'receipt.pick_image': 'Vui lòng chọn file hình ảnh hóa đơn.',
      'receipt.remove': 'Xóa ảnh',

      'budget.limits': 'Hạn mức danh mục',
      'budget.edit_title': 'Chỉnh hạn mức ngân sách',
      'budget.category': 'Danh mục',
      'budget.limit': 'Hạn mức',
      'budget.save': 'Lưu hạn mức',
      'budget.over': 'VƯỢT',
      'budget.over_by': 'Vượt {amount}',
      'budget.weekly': 'Chi tiêu theo tuần',
      'budget.ai_insight': 'Gợi ý từ AI',
      'budget.ai_over': '<b>{category}</b> đang ở mức <b>{pct}%</b> ngân sách. Bạn đã vượt giới hạn — hãy tạm dừng chi mục này đến cuối tháng.',
      'budget.ai_ok': '<b>{category}</b> đang ở mức <b>{pct}%</b> ngân sách. Vẫn nằm trong kiểm soát, tiếp tục giữ nhịp nhé!',
      'budget.invalid': 'Vui lòng nhập hạn mức hợp lệ, lớn hơn 0.',
      'budget.spending_by_category': 'Chi tiêu theo danh mục',
      'budget.week': 'Tuần {n}',
      'budget.ai_none': 'Tháng này chưa có khoản chi đáng kể nào.',
      'budget.alert_email': 'Chi tiêu nhóm <b>{category}</b> đã lên tới <b>{spent}</b>, vượt hạn mức <b>{limit}</b> một khoản <b>{over}</b>.',

      'goal.new': '+ Mục tiêu mới',
      'goal.add_title': 'Thêm mục tiêu mới',
      'goal.name': 'Tên mục tiêu',
      'goal.name_hint': 'VD: Laptop mới',
      'goal.target': 'Mục tiêu',
      'goal.initial': 'Đã tiết kiệm',
      'goal.deadline': 'Hạn chót',
      'goal.deadline_hint': 'VD: Tháng 12/2026',
      'goal.accent': 'Màu nhấn',
      'goal.account': 'Tài khoản riêng (tiền nạp sẽ trừ từ đây)',
      'goal.no_account': 'Không liên kết tài khoản',
      'goal.icon': 'Biểu tượng',
      'goal.save': 'Lưu mục tiêu',
      'goal.deposit': '+ Nạp tiền',
      'goal.deposit_title': 'Nạp tiền vào mục tiêu',
      'goal.deposit_amount': 'Số tiền nạp',
      'goal.confirm_deposit': 'Xác nhận nạp',
      'goal.edit_saved': 'Sửa số tiền đã nạp',
      'goal.complete': 'HOÀN THÀNH ✔',
      'goal.saved_label': 'Đã có:',
      'goal.target_label': 'Mục tiêu:',
      'goal.to_go': '<b>{amount}</b> nữa · khoảng {months} tháng',
      'goal.achieved': '🎉 Đã đạt mục tiêu! Tuyệt vời, {name}.',
      'goal.total_saved': 'Tổng đã tiết kiệm',
      'goal.of_total': 'trên {amount}',
      'goal.completed_count': '🏆 {n} mục tiêu hoàn thành',
      'goal.wallet': 'Ví: {name}',

      'coach.placeholder': 'Hỏi bất cứ điều gì về tài chính của bạn…',
      'coach.send': 'Gửi',
      'coach.notifications': 'Thông báo',
      'coach.quick_prompts': 'Câu hỏi nhanh',
      'coach.history': 'Lịch sử trò chuyện',
      'coach.new_chat': '+ Cuộc trò chuyện mới',
      'coach.no_history': 'Chưa có cuộc trò chuyện nào.',
      'coach.rename': 'Đổi tên',
      'coach.rename_prompt': 'Tên mới cho cuộc trò chuyện:',
      'coach.delete_confirm': 'Xóa cuộc trò chuyện “{title}”?',
      'coach.clear_all': 'Xóa toàn bộ lịch sử',
      'coach.clear_confirm': 'Xóa toàn bộ lịch sử trò chuyện? Hành động này không thể hoàn tác.',
      'coach.greeting': 'Chào {name}! Mình đã xem qua chi tiêu của bạn. Hỏi mình bất cứ điều gì nhé.',
      'coach.thinking': 'Đang phân tích…',
      'coach.msg_count': '{n} tin nhắn',
      'coach.untitled': 'Cuộc trò chuyện mới',
      'coach.prompt1': '📊 Tháng này tôi tiêu thế nào?',
      'coach.prompt2': '🎯 Mục tiêu nào gần đạt nhất?',
      'coach.prompt3': '💰 Ngân sách nào sắp vượt?',
      'coach.prompt4': '🏦 Số dư các tài khoản?',
      'time.now': 'vừa xong',
      'time.minutes': '{n} phút trước',
      'time.hours': '{n} giờ trước',

      'auth.login': 'Đăng nhập',
      'auth.signup': 'Đăng ký',
      'auth.username': 'Tên đăng nhập',
      'auth.username_hint': 'Nhập tên đăng nhập',
      'auth.email': 'Email',
      'auth.password': 'Mật khẩu',
      'auth.confirm': 'Nhập lại mật khẩu',
      'auth.create': 'Tạo tài khoản',
      'settings.title': 'Cài đặt tài khoản',
      'settings.lead': 'Quản lý ngôn ngữ, đơn vị tiền, email thông báo và dữ liệu cá nhân.',
      'settings.identity': 'Thông tin tài khoản',
      'settings.username': 'Tên đăng nhập',
      'settings.email': 'Email',
      'settings.email_status': 'Trạng thái email',
      'settings.verified': '✓ Đã xác minh',
      'settings.unverified': 'Chưa xác minh',
      'settings.display': 'Ngôn ngữ & đơn vị tiền',
      'settings.language_hint': 'Áp dụng cho toàn bộ giao diện và câu trả lời của AI Coach.',
      'settings.currency_hint': 'Số tiền luôn được lưu bằng VND và chỉ quy đổi khi hiển thị.',
      'settings.notifications': 'Thông báo email',
      'settings.weekly': 'Báo cáo chi tiêu hàng tuần',
      'settings.weekly_hint': 'Nhận tổng hợp thu, chi, so sánh tuần trước và các nhóm chi tiêu lớn.',
      'settings.budget_alert': 'Cảnh báo vượt ngân sách',
      'settings.budget_alert_hint': 'Gửi email một lần khi một danh mục vừa vượt hạn mức trong tháng.',
      'settings.save_prefs': 'Lưu tùy chọn',
      'settings.saved': 'Đã lưu tùy chọn.',
      'settings.save_failed': 'Không thể lưu.',
      'settings.danger': 'Xóa tài khoản',
      'settings.danger_hint': 'Xóa vĩnh viễn tài khoản cùng toàn bộ tài khoản tiền, giao dịch, ngân sách, mục tiêu và lịch sử trò chuyện. Dữ liệu không thể khôi phục.',
      'settings.delete_btn': 'Xóa tài khoản',
      'settings.delete_title': 'Xác nhận xóa tài khoản',
      'settings.delete_hint': 'Nhập mật khẩu và chữ <strong>DELETE</strong>. Hành động này không thể hoàn tác.',
      'settings.password': 'Mật khẩu',
      'settings.type_delete': 'Nhập DELETE',
      'settings.delete_forever': 'Xóa vĩnh viễn'
    },

    en: {
      'nav.overview': 'Overview',
      'nav.transactions': 'Transactions',
      'nav.budgets': 'Budgets',
      'nav.goals': 'Goals',
      'nav.coach': 'AI Coach',
      'nav.settings': 'Settings',
      'nav.logout': 'Log out',
      'brand.tagline': '· Smart Finance',
      'common.plan': 'Student',
      'common.synced': 'Synced',
      'common.save': 'Save',
      'common.cancel': 'Cancel',
      'common.delete': 'Delete',
      'common.edit': 'Edit',
      'common.close': 'Close',
      'common.confirm': 'Confirm',
      'common.saving': 'Saving…',
      'common.loading': 'Loading…',
      'common.error': 'Something went wrong',
      'common.none': 'None',
      'common.language': 'Language',
      'common.currency': 'Currency',
      'common.rate_note': 'Amounts are always stored in VND; only the display changes.',

      'page.overview.title': 'Overview',
      'page.overview.sub': 'All accounts synced',
      'page.transactions.title': 'Transactions',
      'page.transactions.sub': 'Every penny in and out',
      'page.budgets.title': 'Budgets',
      'page.budgets.sub': 'All accounts synced',
      'page.goals.title': 'Goals',
      'page.goals.sub': 'Track your savings progress',
      'page.coach.title': 'AI Coach',
      'page.coach.sub': 'Personal smart assistant',

      'kpi.balance': 'BALANCE',
      'kpi.balance.sub': 'Across all accounts',
      'kpi.income': 'INCOME',
      'kpi.income.sub': 'This month',
      'kpi.spending': 'SPENDING',
      'kpi.spending.sub': 'In {month}',
      'kpi.savings_rate': 'SAVINGS RATE',
      'kpi.savings_rate.sub': 'Target {target}%',
      'kpi.total_income': 'TOTAL INCOME',
      'kpi.total_expense': 'TOTAL EXPENSES',
      'kpi.net': 'NET THIS MONTH',
      'kpi.total_budget': 'TOTAL BUDGET',
      'kpi.total_spent': 'TOTAL SPENT',
      'kpi.remaining': 'REMAINING',

      'overview.alert': 'Budget <b>{category}</b> is over — by <b>{amount}</b>',
      'overview.review': 'Review',
      'accounts.title': 'Accounts Overview',
      'accounts.total': 'Total across accounts',
      'accounts.add': '+ Add Account',
      'accounts.add_title': 'Add a new account',
      'accounts.edit_title': 'Edit account',
      'accounts.name': 'Account name',
      'accounts.name_hint': 'e.g. Vietcombank, ZaloPay, Cash wallet',
      'accounts.type': 'Account type',
      'accounts.icon': 'Icon',
      'accounts.opening_balance': 'Opening balance',
      'accounts.active': '● Active',
      'accounts.delete_confirm': 'Delete account “{name}”?',
      'accounts.delete_with_txn': 'Account “{name}” still has {count} transactions. Pick an account to move them to:',
      'accounts.move_to': 'Move transactions to',
      'accounts.deleted': 'Account deleted.',
      'accounts.created': 'Account added.',
      'accounts.updated': 'Account updated.',
      'accounts.edit_balance': 'Edit balance',
      'accounts.balance_title': 'Update balance',
      'accounts.balance_hint': 'Your transaction history stays intact; only the opening balance is adjusted.',
      'accounts.current_balance': 'Current balance',
      'accounts.min_one': 'You need to keep at least one account.',
      'accounts.invalid_balance': 'Please enter a valid balance of 0 or more.',
      'accounts.invalid_name': 'Please enter an account name.',

      'acctype.cash': 'Cash',
      'acctype.bank': 'Bank',
      'acctype.ewallet': 'E-wallet',
      'acctype.credit': 'Credit card',
      'acctype.savings': 'Savings',
      'acctype.investment': 'Investment',
      'acctype.cash.group': '💵 CASH',
      'acctype.bank.group': '🏦 BANK ACCOUNTS',
      'acctype.ewallet.group': '📱 E-WALLETS',
      'acctype.credit.group': '💳 CREDIT CARDS',
      'acctype.savings.group': '🐖 SAVINGS',
      'acctype.investment.group': '📈 INVESTMENTS',

      'txn.add': '+ Add Transaction',
      'txn.add_title': 'Add Transaction',
      'txn.edit_title': 'Edit Transaction',
      'txn.expense': 'Expense',
      'txn.income': 'Income',
      'txn.merchant': 'Merchant / Description',
      'txn.merchant_hint': 'e.g. Highlands Coffee',
      'txn.amount': 'Amount',
      'txn.date': 'Date',
      'txn.category': 'Category',
      'txn.account': 'Paid via / Account',
      'txn.save': 'Save Transaction',
      'txn.save_changes': 'Save changes',
      'txn.search': '🔍  Search merchants, categories, accounts…',
      'txn.export': 'Export CSV',
      'txn.empty': 'No matching transactions yet.',
      'txn.recent': 'Recent Transactions',
      'txn.col.merchant': 'Merchant',
      'txn.col.category': 'Category',
      'txn.col.account': 'Account',
      'txn.col.amount': 'Amount',
      'txn.delete_confirm': 'Delete this transaction? The account balance will be restored.',
      'txn.ai_tagged': 'AI tagged',
      'txn.balance_after': '{account} balance after this transaction:',
      'txn.insufficient': '⚠️ not enough balance',
      'txn.all_categories': 'All categories',
      'txn.from_date': 'From date',
      'txn.to_date': 'To date',

      'receipt.label': 'Attach receipt',
      'receipt.drop': 'Drag & drop or click to upload a receipt',
      'receipt.hint': 'Fields are filled in automatically by AI (JPG, PNG)',
      'receipt.scanning': 'Scanning the receipt…',
      'receipt.done': 'Receipt data extracted!',
      'receipt.failed': 'Could not read the receipt: {error}',
      'receipt.pick_image': 'Please choose an image file of the receipt.',
      'receipt.remove': 'Remove image',

      'budget.limits': 'Category limits',
      'budget.edit_title': 'Edit budget limit',
      'budget.category': 'Category',
      'budget.limit': 'Limit',
      'budget.save': 'Save limit',
      'budget.over': 'OVER',
      'budget.over_by': 'Over by {amount}',
      'budget.weekly': 'Weekly Spend',
      'budget.ai_insight': 'AI Insight',
      'budget.ai_over': '<b>{category}</b> is at <b>{pct}%</b> of its budget. You are over the limit — pause this category until the end of the month.',
      'budget.ai_ok': '<b>{category}</b> is at <b>{pct}%</b> of its budget. Still under control, keep it up!',
      'budget.invalid': 'Please enter a valid limit greater than 0.',
      'budget.spending_by_category': 'Spending by Category',
      'budget.week': 'Wk {n}',
      'budget.ai_none': 'No significant spending recorded yet this month.',
      'budget.alert_email': 'Your spending in <b>{category}</b> has reached <b>{spent}</b>, exceeding your limit of <b>{limit}</b> by <b>{over}</b>.',

      'goal.new': '+ New Goal',
      'goal.add_title': 'Add New Goal',
      'goal.name': 'Goal name',
      'goal.name_hint': 'e.g. New Laptop',
      'goal.target': 'Target',
      'goal.initial': 'Initial saved',
      'goal.deadline': 'Deadline',
      'goal.deadline_hint': 'e.g. Dec 2026',
      'goal.accent': 'Accent colour',
      'goal.account': 'Dedicated account (deposits are taken from here)',
      'goal.no_account': 'No linked account',
      'goal.icon': 'Icon emoji',
      'goal.save': 'Save Goal',
      'goal.deposit': '+ Deposit Funds',
      'goal.deposit_title': 'Deposit into goal',
      'goal.deposit_amount': 'Amount to deposit',
      'goal.confirm_deposit': 'Confirm Deposit',
      'goal.edit_saved': 'Adjust saved amount',
      'goal.complete': 'COMPLETE ✔',
      'goal.saved_label': 'Saved:',
      'goal.target_label': 'Target:',
      'goal.to_go': '<b>{amount}</b> to go · ~{months} months',
      'goal.achieved': '🎉 Goal achieved! Great work, {name}.',
      'goal.total_saved': 'Total Saved Across Goals',
      'goal.of_total': 'of {amount}',
      'goal.completed_count': '🏆 {n} goal completed',
      'goal.wallet': 'Wallet: {name}',

      'coach.placeholder': 'Ask anything about your finances…',
      'coach.send': 'Send',
      'coach.notifications': 'Notifications',
      'coach.quick_prompts': 'Quick Prompts',
      'coach.history': 'Chat history',
      'coach.new_chat': '+ New conversation',
      'coach.no_history': 'No conversations yet.',
      'coach.rename': 'Rename',
      'coach.rename_prompt': 'New name for this conversation:',
      'coach.delete_confirm': 'Delete the conversation “{title}”?',
      'coach.clear_all': 'Clear all history',
      'coach.clear_confirm': 'Delete the entire chat history? This cannot be undone.',
      'coach.greeting': 'Hi {name}! I have looked through your spending. Ask me anything.',
      'coach.thinking': 'Thinking…',
      'coach.msg_count': '{n} messages',
      'coach.untitled': 'New conversation',
      'coach.prompt1': '📊 How did I spend this month?',
      'coach.prompt2': '🎯 Which goal is closest?',
      'coach.prompt3': '💰 Which budget is about to break?',
      'coach.prompt4': '🏦 What are my account balances?',
      'time.now': 'just now',
      'time.minutes': '{n} min ago',
      'time.hours': '{n}h ago',

      'auth.login': 'Sign in',
      'auth.signup': 'Sign up',
      'auth.username': 'Username',
      'auth.username_hint': 'Enter your username',
      'auth.email': 'Email',
      'auth.password': 'Password',
      'auth.confirm': 'Repeat password',
      'auth.create': 'Create account',
      'settings.title': 'Account settings',
      'settings.lead': 'Manage language, currency, email notifications and your personal data.',
      'settings.identity': 'Account details',
      'settings.username': 'Username',
      'settings.email': 'Email',
      'settings.email_status': 'Email status',
      'settings.verified': '✓ Verified',
      'settings.unverified': 'Not verified',
      'settings.display': 'Language & currency',
      'settings.language_hint': 'Applies to the whole interface and to AI Coach replies.',
      'settings.currency_hint': 'Amounts are always stored in VND and only converted for display.',
      'settings.notifications': 'Email notifications',
      'settings.weekly': 'Weekly spending report',
      'settings.weekly_hint': 'A weekly summary of income, spending and your largest categories.',
      'settings.budget_alert': 'Budget overspend alert',
      'settings.budget_alert_hint': 'One email the moment a category goes over its monthly limit.',
      'settings.save_prefs': 'Save preferences',
      'settings.saved': 'Preferences saved.',
      'settings.save_failed': 'Could not save.',
      'settings.danger': 'Delete account',
      'settings.danger_hint': 'Permanently delete your account together with all money accounts, transactions, budgets, goals and chat history. This cannot be undone.',
      'settings.delete_btn': 'Delete account',
      'settings.delete_title': 'Confirm account deletion',
      'settings.delete_hint': 'Enter your password and the word <strong>DELETE</strong>. This cannot be undone.',
      'settings.password': 'Password',
      'settings.type_delete': 'Type DELETE',
      'settings.delete_forever': 'Delete permanently'
    }
  };

  function readStored(key, fallback) {
    try {
      return global.localStorage.getItem(key) || fallback;
    } catch (e) {
      return fallback;
    }
  }

  function writeStored(key, value) {
    try {
      global.localStorage.setItem(key, value);
    } catch (e) {
      /* Private-mode browsers simply keep the server value. */
    }
  }

  var seed = global.BB_PREFS || {};
  var state = {
    lang: '',
    currency: ''
  };

  function currencyMeta(code) {
    for (var i = 0; i < CURRENCIES.length; i++) {
      if (CURRENCIES[i].code === code) return CURRENCIES[i];
    }
    return CURRENCIES[0];
  }

  var BB = {
    LANGUAGES: LANGUAGES,
    CURRENCIES: CURRENCIES,
    listeners: [],

    get lang() { return state.lang; },
    get currency() { return state.currency; },

    meta: function () { return currencyMeta(state.currency); },
    symbol: function () { return this.meta().symbol; },

    setLanguage: function (code, opts) {
      var valid = LANGUAGES.some(function (l) { return l.code === code; });
      state.lang = valid ? code : 'vi';
      writeStored(LANG_KEY, state.lang);
      document.documentElement.setAttribute('lang', state.lang);
      if (!opts || opts.persist !== false) this.persist();
      this.refresh();
    },

    setCurrency: function (code, opts) {
      var valid = CURRENCIES.some(function (c) { return c.code === code; });
      state.currency = valid ? code : 'VND';
      writeStored(CUR_KEY, state.currency);
      if (!opts || opts.persist !== false) this.persist();
      this.refresh();
    },

    /* Saves the choice on the server so it follows the user to other devices. */
    persist: function () {
      try {
        fetch('/api/account/preferences', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ language: state.lang, currency: state.currency })
        }).catch(function () { /* offline is fine, localStorage still holds it */ });
      } catch (e) { /* ignore */ }
    },

    ready: false,

    /* Callbacks registered after init still fire once, so pages that load
       before DOMContentLoaded get a correct first paint. */
    onChange: function (fn) {
      this.listeners.push(fn);
      if (this.ready) {
        try { fn(state.lang, state.currency); } catch (e) { console.error(e); }
      }
    },

    refresh: function () {
      this.applyDom(document);
      this.renderSwitchers();
      this.listeners.forEach(function (fn) {
        try { fn(state.lang, state.currency); } catch (e) { console.error(e); }
      });
    },

    /* ---------- translation ---------- */
    t: function (key, vars) {
      var table = DICT[state.lang] || DICT.vi;
      var text = table[key];
      if (text === undefined) text = (DICT.vi[key] !== undefined ? DICT.vi[key] : key);
      if (vars) {
        Object.keys(vars).forEach(function (name) {
          text = text.split('{' + name + '}').join(String(vars[name]));
        });
      }
      return text;
    },

    /* Translates any element carrying data-i18n / data-i18n-* attributes. */
    applyDom: function (root) {
      root = root || document;
      var self = this;
      root.querySelectorAll('[data-i18n]').forEach(function (el) {
        var key = el.getAttribute('data-i18n');
        if (el.hasAttribute('data-i18n-html')) el.innerHTML = self.t(key);
        else el.textContent = self.t(key);
      });
      root.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
        el.setAttribute('placeholder', self.t(el.getAttribute('data-i18n-placeholder')));
      });
      root.querySelectorAll('[data-i18n-title]').forEach(function (el) {
        el.setAttribute('title', self.t(el.getAttribute('data-i18n-title')));
        if (el.hasAttribute('aria-label')) {
          el.setAttribute('aria-label', self.t(el.getAttribute('data-i18n-title')));
        }
      });
    },

    /* ---------- currency ---------- */
    fromBase: function (vnd) { return Number(vnd || 0) / this.meta().rate; },
    toBase: function (value) { return Number(value || 0) * this.meta().rate; },

    /* Full precision, e.g. "1.450.000 ₫" or "$57.09". */
    full: function (vnd) {
      var meta = this.meta();
      var value = this.fromBase(vnd);
      var locale = state.lang === 'vi' ? 'vi-VN' : 'en-US';
      var text = value.toLocaleString(locale, {
        minimumFractionDigits: meta.decimals,
        maximumFractionDigits: meta.decimals
      });
      return meta.position === 'prefix' ? meta.symbol + text : text + ' ' + meta.symbol;
    },

    /* Compact form used in KPI tiles and charts, e.g. "1.5M ₫". */
    money: function (vnd) {
      var meta = this.meta();
      var value = this.fromBase(vnd);
      var abs = Math.abs(value);
      var text;
      if (abs >= 1e9) text = trim(value / 1e9) + 'B';
      else if (abs >= 1e6) text = trim(value / 1e6) + 'M';
      else if (abs >= 1e3 && meta.decimals === 0) text = Math.round(value / 1e3) + 'K';
      else if (abs >= 1e3) text = trim(value / 1e3) + 'K';
      else text = meta.decimals ? value.toFixed(meta.decimals) : String(Math.round(value));
      return meta.position === 'prefix' ? meta.symbol + text : text + ' ' + meta.symbol;
    },

    /* Bare number for chart axes, no symbol. */
    axis: function (vnd) {
      var value = this.fromBase(vnd);
      var abs = Math.abs(value);
      if (abs >= 1e9) return trim(value / 1e9) + 'B';
      if (abs >= 1e6) return trim(value / 1e6) + 'M';
      if (abs >= 1e3) return trim(value / 1e3) + 'K';
      return String(Math.round(value * 100) / 100);
    },

    /* Sensible step for a number input in the active currency. */
    inputStep: function () {
      var meta = this.meta();
      if (meta.code === 'VND') return 1000;
      if (meta.decimals === 0) return 10;
      return 0.01;
    },

    /* Turns a VND value into the number an input field should show. */
    inputValue: function (vnd) {
      var meta = this.meta();
      var value = this.fromBase(vnd);
      return meta.decimals ? Number(value.toFixed(meta.decimals)) : Math.round(value);
    },

    localeDate: function () { return state.lang === 'vi' ? 'vi-VN' : 'en-US'; },

    /* ---------- switcher widget ---------- */
    renderSwitchers: function () {
      var self = this;
      document.querySelectorAll('[data-bb-switcher]').forEach(function (host) {
        if (!host.dataset.bbBuilt) {
          host.classList.add('bb-switcher');
          host.innerHTML =
            '<label class="bb-sw-item"><span class="bb-sw-ico">🌐</span>' +
            '<select class="bb-sw-select" data-bb-lang aria-label="Language">' +
            LANGUAGES.map(function (l) {
              return '<option value="' + l.code + '">' + l.flag + ' ' + l.label + '</option>';
            }).join('') +
            '</select></label>' +
            '<label class="bb-sw-item"><span class="bb-sw-ico">💱</span>' +
            '<select class="bb-sw-select" data-bb-cur aria-label="Currency">' +
            CURRENCIES.map(function (c) {
              return '<option value="' + c.code + '">' + c.code + ' ' + c.symbol + '</option>';
            }).join('') +
            '</select></label>';
          host.querySelector('[data-bb-lang]').addEventListener('change', function (e) {
            self.setLanguage(e.target.value);
          });
          host.querySelector('[data-bb-cur]').addEventListener('change', function (e) {
            self.setCurrency(e.target.value);
          });
          host.dataset.bbBuilt = '1';
        }
        host.querySelector('[data-bb-lang]').value = state.lang;
        host.querySelector('[data-bb-cur]').value = state.currency;
      });
    },

    init: function () {
      state.lang = seed.language || readStored(LANG_KEY, 'vi');
      state.currency = seed.currency || readStored(CUR_KEY, 'VND');
      if (!LANGUAGES.some(function (l) { return l.code === state.lang; })) state.lang = 'vi';
      if (!CURRENCIES.some(function (c) { return c.code === state.currency; })) state.currency = 'VND';
      writeStored(LANG_KEY, state.lang);
      writeStored(CUR_KEY, state.currency);
      document.documentElement.setAttribute('lang', state.lang);
      injectStyles();
      this.ready = true;
      this.applyDom(document);
      this.renderSwitchers();
      this.listeners.forEach(function (fn) {
        try { fn(state.lang, state.currency); } catch (e) { console.error(e); }
      });
    }
  };

  function trim(n) {
    return (Math.round(n * 10) / 10).toString().replace(/\.0$/, '');
  }

  function injectStyles() {
    if (document.getElementById('bb-switcher-style')) return;
    var css = document.createElement('style');
    css.id = 'bb-switcher-style';
    css.textContent =
      '.bb-switcher{display:flex;gap:8px;align-items:center}' +
      '.bb-sw-item{display:flex;align-items:center;gap:6px;background:#F1F5F9;border:1px solid #E2E8F0;' +
      'border-radius:999px;padding:6px 12px;cursor:pointer;transition:.16s}' +
      '.bb-sw-item:hover{border-color:#0D9488;background:#F0FDFA}' +
      '.bb-sw-ico{font-size:14px;line-height:1}' +
      '.bb-sw-select{border:0;background:transparent;font:inherit;font-size:13px;font-weight:700;' +
      'color:#334155;cursor:pointer;outline:none;padding-right:2px}' +
      '@media(max-width:820px){.bb-sw-item{padding:5px 8px}.bb-sw-select{font-size:12px;max-width:96px}}';
    document.head.appendChild(css);
  }

  global.BB = BB;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { BB.init(); });
  } else {
    BB.init();
  }
})(window);
