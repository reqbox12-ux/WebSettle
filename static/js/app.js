/**
 * 라온스포츠 포털 — SPA Shell
 * Handles routing, auth, and page rendering for the branch portal.
 */
(function () {
  'use strict';

  // ── Auth helpers ──────────────────────────────────────────────
  function getToken() {
    return localStorage.getItem('raon_token') || sessionStorage.getItem('raon_token');
  }
  function getUser() {
    return {
      role:   localStorage.getItem('raon_role')   || 'staff',
      name:   localStorage.getItem('raon_name')   || '',
      branch: localStorage.getItem('raon_branch') || '',
    };
  }
  function logout() {
    fetch('/api/auth/logout', { method: 'POST' }).finally(() => {
      localStorage.removeItem('raon_token');
      localStorage.removeItem('raon_role');
      localStorage.removeItem('raon_name');
      localStorage.removeItem('raon_branch');
      sessionStorage.removeItem('raon_token');
      window.location.href = '/login';
    });
  }
  async function api(path, opts = {}) {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    const resp = await fetch(window.API_BASE + path, { ...opts, headers });
    if (resp.status === 401) { logout(); return null; }
    return resp;
  }

  // ── Router ────────────────────────────────────────────────────
  const PAGES = {
    home:        { label: '홈',      icon: 'home',       staffOnly: false },
    attendance:  { label: '근태',    icon: 'clock',      staffOnly: true  },
    operations:  { label: '운영관리', icon: 'settings',   staffOnly: true  },
    members:     { label: '회원',    icon: 'users',      staffOnly: true  },
    classes:     { label: '수업',    icon: 'calendar',   staffOnly: false },
    instructors: { label: '강사',    icon: 'user-check', staffOnly: false },
  };

  let currentPage = window.INITIAL_PAGE || 'home';
  const user = getUser();

  // Redirect to login if no token
  if (!getToken()) {
    window.location.href = '/login';
  }

  // ── Render Shell ──────────────────────────────────────────────
  function renderShell() {
    const root = document.getElementById('app-root');

    // Build sidebar nav items
    const navItemsHTML = Object.entries(PAGES).map(([key, cfg]) => {
      if (cfg.staffOnly && user.role !== 'staff') return '';
      return `
        <div class="nav-item ${key === currentPage ? 'active' : ''}" onclick="navigateTo('${key}')">
          <i data-lucide="${cfg.icon}" class="nav-icon"></i>
          <span>${cfg.label}</span>
        </div>`;
    }).join('');

    // Bottom tabs for mobile
    const tabsHTML = Object.entries(PAGES).map(([key, cfg]) => {
      if (cfg.staffOnly && user.role !== 'staff') return '';
      return `
        <button class="tab ${key === currentPage ? 'active' : ''}" onclick="navigateTo('${key}')">
          <i data-lucide="${cfg.icon}"></i>
          <span>${cfg.label}</span>
        </button>`;
    }).join('');

    const pageInfo = PAGES[currentPage] || PAGES.home;

    root.innerHTML = `
      <div class="app">
        <nav class="sidebar">
          <div class="brand">
            <div class="brand-mark">라</div>
            <div>
              <div class="brand-name">RAON SPORTS</div>
              <div class="brand-sub">${user.branch || '지점 포털'}</div>
            </div>
          </div>

          <div class="nav-group">
            <div class="nav-label">메뉴</div>
            ${navItemsHTML}
          </div>

          <div class="sidebar-foot">
            <div class="user-card" onclick="logout()">
              <div class="avatar">${(user.name || '?').charAt(0)}</div>
              <div class="user-meta">
                <div class="name">${user.name || '사용자'}</div>
                <div class="role">${user.role === 'staff' ? '직원' : '회원'} · 로그아웃</div>
              </div>
            </div>
          </div>
        </nav>

        <header class="header">
          <div>
            <div class="page-title">${pageInfo.label}</div>
            <div class="crumbs">라온스포츠 · ${user.branch || ''}</div>
          </div>
          <div class="header-spacer"></div>
          <div class="header-action">
            <button class="icon-btn" onclick="toggleTheme()" title="다크모드">
              <i data-lucide="moon"></i>
            </button>
            <div class="avatar" style="cursor:pointer" onclick="logout()">${(user.name || '?').charAt(0)}</div>
          </div>
        </header>

        <main class="main" id="page-content">
          <div class="page">
            <div class="empty">페이지를 불러오는 중…</div>
          </div>
        </main>

        <nav class="bottom-tabs">${tabsHTML}</nav>
      </div>
    `;

    // Initialize Lucide icons
    if (window.lucide) lucide.createIcons();

    // Render page content
    renderPage(currentPage);
  }

  // ── Page Renderers ────────────────────────────────────────────
  async function renderPage(page) {
    const container = document.getElementById('page-content');
    if (!container) return;

    switch (page) {
      case 'home':        await renderHome(container);        break;
      case 'attendance':  await renderAttendance(container);  break;
      case 'operations':  await renderOperations(container);  break;
      case 'members':     await renderMembers(container);     break;
      case 'classes':     await renderClasses(container);     break;
      case 'instructors': await renderInstructors(container); break;
      default:            renderNotFound(container);
    }
    if (window.lucide) lucide.createIcons();
  }

  // ── Home Page ─────────────────────────────────────────────────
  async function renderHome(container) {
    container.innerHTML = '<div class="page"><div class="empty">홈 로딩 중…</div></div>';
    try {
      const resp = await api('/api/home/data');
      if (!resp) return;
      const data = await resp.json();
      const { announcements = [], events = [], classes = [] } = data;

      // Marquee
      const marqueeText = announcements.length
        ? announcements.map(a => a.title).join('    ·    ')
        : '라온스포츠 포털에 오신 것을 환영합니다';
      const doubledText = marqueeText + '    ·    ' + marqueeText;

      // Events hero
      const ev = events[0];
      const heroHTML = ev ? `
        <div class="hero-main" style="background-image:url('${ev.image_path || ''}')">
          ${ev.eyebrow ? `<div class="eyebrow"><i data-lucide="zap" style="width:12px;height:12px"></i> ${ev.eyebrow}</div>` : ''}
          <h2>${ev.title}</h2>
          <p>${ev.sub || ''}</p>
          <button class="btn primary sm" onclick="openEvent(${ev.id})">자세히 보기 →</button>
        </div>
      ` : `
        <div class="hero-main" style="background:#1a1410">
          <h2>라온스포츠에 오신 것을 환영합니다</h2>
          <p>최신 이벤트와 프로그램을 확인해 보세요.</p>
        </div>
      `;

      // Side cards
      const sideEvs = events.slice(1, 3);
      const sideHTML = sideEvs.map(ev => `
        <div class="hero-side-card" style="cursor:pointer" onclick="openEvent(${ev.id})">
          <div class="deadline"><i data-lucide="calendar" style="width:12px;height:12px"></i> ${ev.ends_at || ''}</div>
          <h3>${ev.title}</h3>
          <p class="muted" style="font-size:13px;margin-top:4px">${(ev.sub || '').slice(0, 60)}</p>
        </div>
      `).join('') || '<div class="hero-side-card"><p class="muted">진행중인 이벤트가 없습니다</p></div><div class="hero-side-card dark"><p>새 이벤트를 기대해 주세요</p></div>';

      // Classes
      const classHTML = classes.map(c => `
        <div class="class-card">
          <div class="thumb" style="background:linear-gradient(135deg,#E0382B22,#1a141022)">
            <div class="corner"><span class="badge red">${c.days || ''}</span></div>
          </div>
          <div class="meta">
            <div class="title">${c.class_name}</div>
            <div class="row">
              <i data-lucide="clock" style="width:13px;height:13px"></i>
              <span>${c.start_time} ~ ${c.end_time}</span>
            </div>
            <div class="row">
              <i data-lucide="user" style="width:13px;height:13px"></i>
              <span>${c.instructor_name || '-'}</span>
            </div>
          </div>
        </div>
      `).join('') || '<div class="empty">등록된 수업이 없습니다</div>';

      container.innerHTML = `
        <div class="page">
          <div class="marquee">
            <div class="marquee-track">${doubledText}</div>
          </div>
          <div class="hero-grid">
            ${heroHTML}
            <div class="hero-side">${sideHTML}</div>
          </div>
          <div style="margin-top:28px">
            <div class="card-head">
              <div>
                <div class="section-title">오늘의 수업</div>
                <div class="section-sub">현재 운영 중인 GX 프로그램</div>
              </div>
            </div>
            <div class="class-grid">${classHTML}</div>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="page"><div class="empty">홈 데이터를 불러올 수 없습니다: ${err.message}</div></div>`;
    }
    if (window.lucide) lucide.createIcons();
  }

  // ── Attendance Page ───────────────────────────────────────────
  async function renderAttendance(container) {
    container.innerHTML = '<div class="page"><div class="empty">근태 로딩 중…</div></div>';
    if (user.role !== 'staff') {
      container.innerHTML = '<div class="page"><div class="empty">직원 전용 메뉴입니다</div></div>';
      return;
    }
    try {
      const today = new Date().toISOString().slice(0, 10);
      const resp = await api('/api/attendance/today');
      if (!resp) return;
      const record = await resp.json();

      const clockInBtn  = record.clock_in  ? `<button class="btn" disabled>출근 완료 ${record.clock_in}</button>` :
                          `<button class="btn primary" onclick="clockIn()"><i data-lucide="log-in"></i> 출근</button>`;
      const clockOutBtn = record.clock_in && !record.clock_out
                          ? `<button class="btn ink" onclick="clockOut()"><i data-lucide="log-out"></i> 퇴근</button>` : '';

      container.innerHTML = `
        <div class="page">
          <div class="section-title">근태 관리</div>
          <div class="section-sub">오늘 ${today} · ${user.name}</div>

          <div class="grid-2" style="margin-bottom:22px;max-width:600px">
            <div class="stat">
              <div class="label">출근 시간</div>
              <div class="value" style="font-size:24px">${record.clock_in || '—'}</div>
            </div>
            <div class="stat">
              <div class="label">퇴근 시간</div>
              <div class="value" style="font-size:24px">${record.clock_out || '—'}</div>
            </div>
          </div>

          <div class="row" style="gap:10px;margin-bottom:28px">
            ${clockInBtn}
            ${clockOutBtn}
          </div>

          <div class="card">
            <div class="card-head"><div class="card-title">이번 달 근태</div></div>
            <div id="monthlyAttendance"><div class="empty">불러오는 중…</div></div>
          </div>
        </div>
      `;
      if (window.lucide) lucide.createIcons();
      loadMonthlyAttendance();
    } catch (err) {
      container.innerHTML = `<div class="page"><div class="empty">오류: ${err.message}</div></div>`;
    }
  }

  async function loadMonthlyAttendance() {
    const now = new Date();
    const resp = await api(`/api/attendance/monthly?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
    if (!resp) return;
    const records = await resp.json();
    const el = document.getElementById('monthlyAttendance');
    if (!el) return;
    if (!records.length) { el.innerHTML = '<div class="empty">이번 달 근태 기록이 없습니다</div>'; return; }
    el.innerHTML = `
      <table class="table">
        <thead><tr><th>날짜</th><th>출근</th><th>퇴근</th><th>근무(분)</th><th>상태</th></tr></thead>
        <tbody>
          ${records.map(r => `
            <tr>
              <td>${r.work_date}</td>
              <td>${r.clock_in || '—'}</td>
              <td>${r.clock_out || '—'}</td>
              <td>${r.work_minutes || 0}</td>
              <td><span class="badge ${r.status === 'late' ? 'warn' : 'ok'}">${r.status === 'late' ? '지각' : '정상'}</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>`;
  }

  window.clockIn = async function () {
    const now = new Date();
    const time = now.toTimeString().slice(0, 5);
    const resp = await api('/api/attendance/clock-in', {
      method: 'POST',
      body: JSON.stringify({ time })
    });
    if (resp && resp.ok) { showToast('출근 처리되었습니다 ' + time); navigateTo('attendance'); }
    else { const d = await resp.json(); showToast(d.detail || '오류', 'err'); }
  };

  window.clockOut = async function () {
    const now = new Date();
    const time = now.toTimeString().slice(0, 5);
    const resp = await api('/api/attendance/clock-out', {
      method: 'POST',
      body: JSON.stringify({ time })
    });
    if (resp && resp.ok) { showToast('퇴근 처리되었습니다 ' + time); navigateTo('attendance'); }
    else { const d = await resp.json(); showToast(d.detail || '오류', 'err'); }
  };

  // ── Operations Page ───────────────────────────────────────────
  async function renderOperations(container) {
    if (user.role !== 'staff') {
      container.innerHTML = '<div class="page"><div class="empty">직원 전용 메뉴입니다</div></div>';
      return;
    }
    container.innerHTML = `
      <div class="page">
        <div class="section-title">운영 관리</div>
        <div class="section-sub">재고 · 비품요청 · A/S · 이벤트 · 공지</div>
        <div class="tabs line" style="margin-bottom:22px" id="opsTabs">
          <button class="on" onclick="showOpsTab('inventory', this)">재고</button>
          <button onclick="showOpsTab('supply', this)">비품 요청</button>
          <button onclick="showOpsTab('as', this)">A/S</button>
          <button onclick="showOpsTab('events', this)">이벤트</button>
          <button onclick="showOpsTab('announcements', this)">공지사항</button>
          <button onclick="showOpsTab('instructors', this)">강사 관리</button>
        </div>
        <div id="opsContent"><div class="empty">불러오는 중…</div></div>
      </div>
    `;
    showOpsTab('inventory');
  }

  window.showOpsTab = async function (tab, btnEl) {
    if (btnEl) {
      document.querySelectorAll('#opsTabs button').forEach(b => b.classList.remove('on'));
      btnEl.classList.add('on');
    }
    const content = document.getElementById('opsContent');
    if (!content) return;
    content.innerHTML = '<div class="empty">불러오는 중…</div>';
    const branch = user.branch || '';

    try {
      if (tab === 'inventory') {
        const resp = await api(`/api/operations/inventory?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">재고 목록</div>
            <button class="btn primary sm" onclick="addInventoryItem()"><i data-lucide="plus"></i> 추가</button>
          </div>
          <table class="table">
            <thead><tr><th>품목</th><th>분류</th><th>수량</th><th>최소수량</th><th>단위</th><th>조작</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td>${i.item_name}</td><td>${i.category}</td>
                  <td><b>${i.quantity}</b></td><td>${i.min_quantity}</td><td>${i.unit}</td>
                  <td>
                    <button class="btn sm" onclick="adjustItem(${i.id},'in')">입고</button>
                    <button class="btn sm" onclick="adjustItem(${i.id},'out')">출고</button>
                  </td>
                </tr>`).join('') || '<tr><td colspan="6" style="text-align:center;color:var(--muted)">재고 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();

      } else if (tab === 'supply') {
        const resp = await api(`/api/operations/supply?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">비품 요청</div>
            <button class="btn primary sm" onclick="newSupplyRequest()"><i data-lucide="plus"></i> 요청</button>
          </div>
          <table class="table">
            <thead><tr><th>품목</th><th>수량</th><th>상태</th><th>요청일</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td>${i.item_name}</td><td>${i.quantity} ${i.unit}</td>
                  <td><span class="badge ${i.status === 'approved' ? 'ok' : i.status === 'rejected' ? 'red' : 'warn'}">${i.status}</span></td>
                  <td>${i.created_at ? i.created_at.slice(0,10) : ''}</td>
                </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;color:var(--muted)">요청 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();

      } else if (tab === 'as') {
        const resp = await api(`/api/operations/as?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">A/S 요청</div>
            <button class="btn primary sm" onclick="newAsRequest()"><i data-lucide="plus"></i> 요청</button>
          </div>
          <table class="table">
            <thead><tr><th>제목</th><th>우선순위</th><th>상태</th><th>등록일</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td>${i.title}</td>
                  <td><span class="prio prio-${i.priority === 'urgent' ? 'urgent' : i.priority === 'low' ? 'low' : 'normal'}">${i.priority}</span></td>
                  <td><span class="badge ${i.status === 'done' ? 'ok' : 'warn'}">${i.status}</span></td>
                  <td>${i.created_at ? i.created_at.slice(0,10) : ''}</td>
                </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;color:var(--muted)">요청 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();

      } else if (tab === 'events') {
        const resp = await api(`/api/operations/events?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">이벤트 관리</div>
            <button class="btn primary sm" onclick="newEvent()"><i data-lucide="plus"></i> 이벤트 추가</button>
          </div>
          <table class="table">
            <thead><tr><th>제목</th><th>마감일</th><th>활성</th><th>등록일</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td>${i.title}</td><td>${i.ends_at || '—'}</td>
                  <td><span class="badge ${i.is_active ? 'ok' : 'outline'}">${i.is_active ? '활성' : '비활성'}</span></td>
                  <td>${i.created_at ? i.created_at.slice(0,10) : ''}</td>
                </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;color:var(--muted)">이벤트 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();

      } else if (tab === 'announcements') {
        const resp = await api(`/api/operations/announcements?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">공지사항</div>
            <button class="btn primary sm" onclick="newAnnouncement()"><i data-lucide="plus"></i> 공지 추가</button>
          </div>
          <table class="table">
            <thead><tr><th>제목</th><th>우선순위</th><th>대상</th><th>만료일</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td>${i.title}</td>
                  <td><span class="badge ${i.priority === 'urgent' ? 'red' : 'outline'}">${i.priority}</span></td>
                  <td>${i.target_branch === 'all' ? '전체' : i.target_branch}</td>
                  <td>${i.expires_at || '—'}</td>
                </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;color:var(--muted)">공지 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();

      } else if (tab === 'instructors') {
        const resp = await api(`/api/operations/instructors?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">강사 관리</div>
            <button class="btn primary sm" onclick="newInstructor()"><i data-lucide="plus"></i> 강사 추가</button>
          </div>
          <div class="grid-3">
            ${items.map(i => `
              <div class="instructor-card">
                <div class="photo" style="${i.photo_path ? 'background-image:url(' + i.photo_path + ')' : 'background:var(--surface-2)'}">
                  <div class="name-overlay">
                    <div class="name">${i.name}</div>
                    <div style="font-size:12px;opacity:.8">${i.english || ''}</div>
                  </div>
                </div>
                <div class="body">
                  <span class="badge outline">${i.role || ''}</span>
                  <p style="margin:8px 0 0;font-size:13px;color:var(--muted)">${(i.bio || '').slice(0,80)}</p>
                </div>
              </div>`).join('') || '<div class="empty" style="grid-column:1/-1">강사 없음</div>'}
          </div>`;
        if (window.lucide) lucide.createIcons();
      }
    } catch (err) {
      content.innerHTML = `<div class="empty">오류: ${err.message}</div>`;
    }
  };

  // Simple prompt-based forms (full modal forms would be added in production)
  window.addInventoryItem = async function () {
    const name = prompt('품목명');
    if (!name) return;
    const qty = parseInt(prompt('초기 수량', '0') || '0', 10);
    const unit = prompt('단위', '개') || '개';
    await api('/api/operations/inventory', {
      method: 'POST',
      body: JSON.stringify({ branch: user.branch, item_name: name, quantity: qty, unit })
    });
    showOpsTab('inventory');
  };
  window.adjustItem = async function (id, type) {
    const qty = parseInt(prompt(type === 'in' ? '입고 수량' : '출고 수량', '1') || '1', 10);
    if (!qty) return;
    await api(`/api/operations/inventory/${id}/adjust`, {
      method: 'POST',
      body: JSON.stringify({ type, qty, note: '' })
    });
    showOpsTab('inventory');
  };
  window.newSupplyRequest = async function () {
    const name = prompt('품목명');
    if (!name) return;
    const qty = parseInt(prompt('수량', '1') || '1', 10);
    await api('/api/operations/supply', {
      method: 'POST',
      body: JSON.stringify({ branch: user.branch, item_name: name, quantity: qty, created_name: user.name })
    });
    showOpsTab('supply');
  };
  window.newAsRequest = async function () {
    const title = prompt('요청 제목');
    if (!title) return;
    const desc = prompt('상세 설명') || '';
    await api('/api/operations/as', {
      method: 'POST',
      body: JSON.stringify({ branch: user.branch, title, description: desc, created_name: user.name })
    });
    showOpsTab('as');
  };
  window.newEvent = async function () {
    const title = prompt('이벤트 제목');
    if (!title) return;
    const sub = prompt('부제목') || '';
    const ends_at = prompt('마감일 (YYYY-MM-DD)') || '';
    const fd = new FormData();
    fd.append('title', title); fd.append('content', sub);
    fd.append('eyebrow', '이벤트'); fd.append('ends_at', ends_at);
    fd.append('branch', user.branch || '');
    const token = getToken();
    await fetch('/api/operations/events', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token },
      body: fd
    });
    showOpsTab('events');
  };
  window.newAnnouncement = async function () {
    const title = prompt('공지 제목');
    if (!title) return;
    const content = prompt('내용') || '';
    await api('/api/operations/announcements', {
      method: 'POST',
      body: JSON.stringify({ title, content, created_by: user.name, target_branch: user.branch || 'all' })
    });
    showOpsTab('announcements');
  };
  window.newInstructor = async function () {
    const name = prompt('강사 이름');
    if (!name) return;
    const role = prompt('역할 (예: GX강사)') || '';
    const fd = new FormData();
    fd.append('name', name); fd.append('role', role);
    fd.append('branch', user.branch || '');
    const token = getToken();
    await fetch('/api/operations/instructors', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token },
      body: fd
    });
    showOpsTab('instructors');
  };
  window.openEvent = function (id) {
    showToast('이벤트 상세보기 준비 중');
  };

  // ── Members Page ──────────────────────────────────────────────
  async function renderMembers(container) {
    if (user.role !== 'staff') {
      container.innerHTML = '<div class="page"><div class="empty">직원 전용 메뉴입니다</div></div>';
      return;
    }
    container.innerHTML = `
      <div class="page">
        <div class="card-head">
          <div>
            <div class="section-title">회원 관리</div>
            <div class="section-sub">${user.branch}</div>
          </div>
          <button class="btn primary" onclick="newMember()"><i data-lucide="user-plus"></i> 신규 등록</button>
        </div>
        <div class="row" style="margin-bottom:14px;gap:8px">
          <input class="input" id="memberSearch" placeholder="이름 또는 전화번호 검색…" style="max-width:280px"
                 oninput="searchMembers(this.value)">
        </div>
        <div id="memberList"><div class="empty">불러오는 중…</div></div>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    loadMembers('');
  }

  async function loadMembers(q) {
    const branch = user.branch || '';
    const resp = await api(`/api/members?branch=${encodeURIComponent(branch)}&q=${encodeURIComponent(q)}`);
    if (!resp) return;
    const members = await resp.json();
    const el = document.getElementById('memberList');
    if (!el) return;
    el.innerHTML = `
      <table class="table">
        <thead><tr><th>이름</th><th>전화번호</th><th>가입일</th><th>상태</th></tr></thead>
        <tbody>
          ${members.map(m => `
            <tr class="row-hover" onclick="viewMember(${m.id})">
              <td><b>${m.name}</b></td>
              <td>${m.phone || '—'}</td>
              <td>${m.join_date || '—'}</td>
              <td><span class="badge ${m.status === 'active' ? 'ok' : 'outline'}">${m.status === 'active' ? '활성' : '비활성'}</span></td>
            </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;color:var(--muted)">회원 없음</td></tr>'}
        </tbody>
      </table>`;
  }

  window.searchMembers = function (q) { loadMembers(q); };
  window.viewMember = function (id) { showToast('회원 상세 준비 중 (ID: ' + id + ')'); };
  window.newMember = async function () {
    const name = prompt('회원 이름');
    if (!name) return;
    const phone = prompt('전화번호') || '';
    await api('/api/members', {
      method: 'POST',
      body: JSON.stringify({ branch: user.branch, name, phone })
    });
    showToast('회원 등록 완료');
    loadMembers('');
  };

  // ── Classes Page ──────────────────────────────────────────────
  async function renderClasses(container) {
    container.innerHTML = '<div class="page"><div class="empty">수업 로딩 중…</div></div>';
    try {
      const branch = user.branch || '';
      const resp = await api(`/api/classes?branch=${encodeURIComponent(branch)}`);
      if (!resp) return;
      const classes = await resp.json();
      const addBtn = user.role === 'staff'
        ? `<button class="btn primary sm" onclick="newClass()"><i data-lucide="plus"></i> 수업 추가</button>` : '';
      container.innerHTML = `
        <div class="page">
          <div class="card-head">
            <div>
              <div class="section-title">수업 시간표</div>
              <div class="section-sub">${branch} · 현재 운영 중인 프로그램</div>
            </div>
            ${addBtn}
          </div>
          <div class="class-grid">
            ${classes.map(c => `
              <div class="class-card">
                <div class="thumb" style="background:linear-gradient(135deg,#E0382B22,#1a141022)">
                  <div class="corner"><span class="badge red">${c.days || '매일'}</span></div>
                </div>
                <div class="meta">
                  <div class="title">${c.class_name}</div>
                  <div class="row">
                    <i data-lucide="clock" style="width:13px;height:13px"></i>
                    <span>${c.start_time} ~ ${c.end_time}</span>
                  </div>
                  <div class="row">
                    <i data-lucide="user" style="width:13px;height:13px"></i>
                    <span>${c.instructor_name || '강사 미배정'}</span>
                  </div>
                  <div class="row">
                    <i data-lucide="users" style="width:13px;height:13px"></i>
                    <span>정원 ${c.capacity}명</span>
                  </div>
                </div>
              </div>`).join('') || '<div class="empty" style="grid-column:1/-1">등록된 수업이 없습니다</div>'}
          </div>
        </div>`;
      if (window.lucide) lucide.createIcons();
    } catch (err) {
      container.innerHTML = `<div class="page"><div class="empty">오류: ${err.message}</div></div>`;
    }
  }

  window.newClass = async function () {
    const name = prompt('수업 이름');
    if (!name) return;
    const start = prompt('시작시간 (HH:MM)', '10:00') || '10:00';
    const end   = prompt('종료시간 (HH:MM)', '11:00') || '11:00';
    await api('/api/classes', {
      method: 'POST',
      body: JSON.stringify({ branch: user.branch, class_name: name, start_time: start, end_time: end })
    });
    showToast('수업 등록 완료');
    renderClasses(document.getElementById('page-content'));
  };

  // ── Instructors Page ──────────────────────────────────────────
  async function renderInstructors(container) {
    container.innerHTML = '<div class="page"><div class="empty">강사 로딩 중…</div></div>';
    try {
      const branch = user.branch || '';
      const resp = await api(`/api/operations/instructors?branch=${encodeURIComponent(branch)}`);
      if (!resp) return;
      const instructors = await resp.json();
      const addBtn = user.role === 'staff'
        ? `<button class="btn primary sm" onclick="newInstructor()"><i data-lucide="plus"></i> 강사 추가</button>` : '';
      container.innerHTML = `
        <div class="page">
          <div class="card-head">
            <div>
              <div class="section-title">강사 소개</div>
              <div class="section-sub">라온스포츠 전문 트레이너</div>
            </div>
            ${addBtn}
          </div>
          <div class="grid-3">
            ${instructors.map(i => `
              <div class="instructor-card">
                <div class="photo" style="${i.photo_path ? 'background-image:url(' + i.photo_path + ')' : 'background:var(--surface-2)'}">
                  <div class="name-overlay">
                    <div class="name">${i.name}</div>
                    <div style="font-size:12px;opacity:.8">${i.english || ''}</div>
                  </div>
                </div>
                <div class="body">
                  <span class="badge outline">${i.role || ''}</span>
                  <p style="margin:8px 0 4px;font-size:13px;color:var(--muted-2)">${(i.bio || '').slice(0, 100)}</p>
                </div>
              </div>`).join('') || '<div class="empty" style="grid-column:1/-1">등록된 강사가 없습니다</div>'}
          </div>
        </div>`;
      if (window.lucide) lucide.createIcons();
    } catch (err) {
      container.innerHTML = `<div class="page"><div class="empty">오류: ${err.message}</div></div>`;
    }
  }

  function renderNotFound(container) {
    container.innerHTML = '<div class="page"><div class="empty">페이지를 찾을 수 없습니다</div></div>';
  }

  // ── Navigation ────────────────────────────────────────────────
  window.navigateTo = function (page) {
    const cfg = PAGES[page];
    if (!cfg) return;
    if (cfg.staffOnly && user.role !== 'staff') {
      showToast('직원 전용 메뉴입니다', 'err');
      return;
    }
    currentPage = page;
    history.pushState({ page }, '', '/' + page);
    renderShell();
  };

  window.addEventListener('popstate', e => {
    if (e.state && e.state.page) {
      currentPage = e.state.page;
      renderShell();
    }
  });

  // ── Toast ─────────────────────────────────────────────────────
  function showToast(msg, type = 'ok') {
    let stack = document.querySelector('.toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      document.body.appendChild(stack);
    }
    const t = document.createElement('div');
    t.className = 'toast';
    t.innerHTML = `<i data-lucide="${type === 'err' ? 'alert-circle' : 'check-circle'}" class="ic"></i> ${msg}`;
    stack.appendChild(t);
    if (window.lucide) lucide.createIcons();
    setTimeout(() => t.remove(), 3500);
  }

  // ── Theme toggle ──────────────────────────────────────────────
  window.toggleTheme = function () {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('raon_theme', isDark ? 'light' : 'dark');
  };

  window.logout = logout;

  // ── Boot ──────────────────────────────────────────────────────
  renderShell();
})();
