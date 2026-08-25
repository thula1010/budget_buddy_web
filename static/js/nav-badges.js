(function () {
  'use strict';

  const sections = ['overview', 'transactions', 'budgets', 'goals', 'ai-coach'];
  let lastState = null;
  let storageKey = '';

  function currentSection() {
    const path = window.location.pathname.replace(/\/+$/, '') || '/';
    if (path === '/transactions') return 'transactions';
    if (path === '/budgets') return 'budgets';
    if (path === '/goals') return 'goals';
    if (path === '/ai-coach') return 'ai-coach';
    return 'overview';
  }

  function hash(value) {
    const text = JSON.stringify(value);
    let result = 2166136261;
    for (let index = 0; index < text.length; index += 1) {
      result ^= text.charCodeAt(index);
      result = Math.imul(result, 16777619);
    }
    return (result >>> 0).toString(36);
  }

  function signatures(state) {
    const transactions = Array.isArray(state.transactions) ? state.transactions : [];
    const budgets = Array.isArray(state.budgets) ? state.budgets : [];
    const goals = Array.isArray(state.goals) ? state.goals : [];
    const notifications = Array.isArray(state.notifications) ? state.notifications : [];
    const noteworthyBudgets = budgets.filter(budget =>
      Number(budget.over) > 0 || Number(budget.pct) >= 80
    );

    return {
      overview: hash({period: state.period, kpi: state.kpi, notifications}),
      transactions: transactions.length ? hash(transactions.map(item => [
        item.id, item.amount, item.date, item.merchant, item.account_id, item.category_id
      ])) : '',
      budgets: noteworthyBudgets.length ? hash(noteworthyBudgets.map(item => [
        item.id, item.category_id, item.period, item.spent, item.limit_vnd, item.pct, item.over
      ])) : '',
      goals: goals.length ? hash(goals.map(item => [
        item.id, item.name, item.current_saved ?? item.saved, item.target, item.deadline, item.account_id
      ])) : '',
      'ai-coach': notifications.length ? hash(notifications.map(item => [
        item.id, item.kind, item.text, item.ago
      ])) : ''
    };
  }

  function readSeen() {
    try {
      const value = JSON.parse(window.localStorage.getItem(storageKey) || '{}');
      return value && typeof value === 'object' ? value : {};
    } catch (error) {
      return {};
    }
  }

  function writeSeen(value) {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(value));
    } catch (error) {
      // Badges still work for the current page when browser storage is unavailable.
    }
  }

  function ensureStyles() {
    if (document.getElementById('bbNavBadgeStyles')) return;
    const style = document.createElement('style');
    style.id = 'bbNavBadgeStyles';
    style.textContent = `
      .nav-unread-dot {
        width: 8px; height: 8px; border-radius: 50%; margin-left: auto; flex: 0 0 8px;
        background: #F43F5E; box-shadow: 0 0 0 3px rgba(244,63,94,.12);
        opacity: 0; transform: scale(.55); transition: opacity .16s, transform .16s;
      }
      .nav-unread-dot.visible { opacity: 1; transform: scale(1); }
      @media (prefers-reduced-motion: no-preference) {
        .nav-unread-dot.visible { animation: bbBadgePulse 2s ease-in-out infinite; }
      }
      @keyframes bbBadgePulse { 0%,100% { box-shadow:0 0 0 3px rgba(244,63,94,.12); } 50% { box-shadow:0 0 0 5px rgba(244,63,94,.04); } }
    `;
    document.head.appendChild(style);
  }

  function ensureDots() {
    ensureStyles();
    document.querySelectorAll('[data-nav-section]').forEach(item => {
      if (item.querySelector('.nav-unread-dot')) return;
      const dot = document.createElement('i');
      dot.className = 'nav-unread-dot';
      dot.setAttribute('aria-hidden', 'true');
      item.appendChild(dot);
    });
  }

  function update(state) {
    if (!state || !state.user) return;
    lastState = state;
    const identity = state.user.email || state.user.name || 'user';
    storageKey = `budget-buddy-nav-seen-v1:${identity}`;
    const values = signatures(state);
    const seen = readSeen();
    const active = currentSection();
    seen[active] = values[active];
    writeSeen(seen);
    ensureDots();

    sections.forEach(section => {
      const item = document.querySelector(`[data-nav-section="${section}"]`);
      if (!item) return;
      const dot = item.querySelector('.nav-unread-dot');
      const visible = section !== active && Boolean(values[section]) && seen[section] !== values[section];
      dot.classList.toggle('visible', visible);
      item.toggleAttribute('data-has-new-updates', visible);
      if (visible) {
        item.title = window.BB && BB.language === 'vi' ? 'Có thông tin mới' : 'New updates';
      } else if (item.title === 'Có thông tin mới' || item.title === 'New updates') {
        item.removeAttribute('title');
      }
    });
  }

  window.BBNavBadges = { update };
  window.addEventListener('storage', () => {
    if (lastState) update(lastState);
  });
})();
