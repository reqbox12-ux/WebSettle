/**
 * 라온스포츠 포털 — SPA Shell v3.1
 * Modal-based forms, hash routing, auth helpers
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
      ['raon_token','raon_role','raon_name','raon_branch'].forEach(k => {
        localStorage.removeItem(k);
        sessionStorage.removeItem(k);
      });
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
  async function apiForm(path, formData, method = 'POST') {
    const token = getToken();
    const headers = {};
    if (token) headers['Authorization'] = 'Bearer ' + token;
    return fetch(window.API_BASE + path, { method, headers, body: formData });
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

  if (!getToken()) { window.location.href = '/login'; }

  // ── Modal System ──────────────────────────────────────────────
  /**
   * createModal({ title, fields, onSubmit, submitLabel, size })
   * fields: [{ id, label, type, placeholder, required, options, hint, accept, row }]
   * type: text | textarea | number | date | time | select | radio | file | hidden
   */
  function createModal({ title, fields = [], onSubmit, submitLabel = '저장', size = '' }) {
    closeModal();

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'modal-overlay';
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });

    const modal = document.createElement('div');
    modal.className = 'modal' + (size === 'lg' ? ' modal-lg' : '');

    // Group consecutive fields with same row key
    let bodyHTML = '';
    let i = 0;
    while (i < fields.length) {
      const f = fields[i];
      if (f.type === 'hidden') { i++; continue; }
      if (f.row && i + 1 < fields.length && fields[i+1].row === f.row) {
        bodyHTML += `<div class="form-row">${fieldHTML(f)}${fieldHTML(fields[i+1])}</div>`;
        i += 2;
      } else {
        bodyHTML += fieldHTML(f);
        i++;
      }
    }

    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">${title}</div>
        <button class="modal-close" onclick="closeModal()">
          <i data-lucide="x" style="width:18px;height:18px"></i>
        </button>
      </div>
      <div class="modal-body">${bodyHTML}</div>
      <div class="modal-footer">
        <button class="btn" onclick="closeModal()">취소</button>
        <button class="btn primary" id="modal-submit">${submitLabel}</button>
      </div>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    if (window.lucide) lucide.createIcons();

    // Radio button interaction
    modal.querySelectorAll('.radio-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const name = btn.querySelector('input').name;
        modal.querySelectorAll(`.radio-btn input[name="${name}"]`).forEach(inp => {
          inp.closest('.radio-btn').classList.remove('selected');
        });
        btn.querySelector('input').checked = true;
        btn.classList.add('selected');
      });
    });

    // File preview
    modal.querySelectorAll('input[type=file]').forEach(inp => {
      inp.addEventListener('change', () => {
        const file = inp.files[0];
        if (!file) return;
        const prev = inp.closest('.file-upload-area').querySelector('.file-preview');
        if (prev && file.type.startsWith('image/')) {
          const reader = new FileReader();
          reader.onload = e => { prev.src = e.target.result; prev.style.display = 'block'; };
          reader.readAsDataURL(file);
        }
        inp.closest('.file-upload-area').querySelector('.file-label').textContent = file.name;
      });
    });

    // Submit handler
    modal.querySelector('#modal-submit').addEventListener('click', async () => {
      const data = {};
      let hasFile = false;
      fields.forEach(f => {
        if (f.type === 'radio') {
          const checked = modal.querySelector(`input[name="${f.id}"]:checked`);
          data[f.id] = checked ? checked.value : (f.options[0]?.value || f.options[0]);
        } else if (f.type === 'file') {
          const inp = modal.querySelector(`#modal-${f.id}`);
          data[f.id] = inp?.files[0] || null;
          if (data[f.id]) hasFile = true;
        } else if (f.type === 'hidden') {
          data[f.id] = f.value;
        } else {
          const el = modal.querySelector(`#modal-${f.id}`);
          data[f.id] = el ? el.value.trim() : '';
        }
        if (f.required && !data[f.id]) {
          modal.querySelector(`#modal-${f.id}`)?.focus();
        }
      });
      const btn = modal.querySelector('#modal-submit');
      btn.disabled = true;
      btn.textContent = '처리 중…';
      try {
        await onSubmit(data, hasFile);
        closeModal();
      } catch (err) {
        showToast(err.message || '오류가 발생했습니다', 'err');
        btn.disabled = false;
        btn.textContent = submitLabel;
      }
    });

    // Focus first input
    setTimeout(() => {
      const first = modal.querySelector('.form-control');
      if (first) first.focus();
    }, 150);
  }

  function fieldHTML(f) {
    const req = f.required ? '<span class="req">*</span>' : '';
    const hint = f.hint ? `<div class="form-hint">${f.hint}</div>` : '';
    let inner = '';

    if (f.type === 'textarea') {
      inner = `<textarea class="form-control" id="modal-${f.id}" placeholder="${f.placeholder||''}" rows="${f.rows||3}">${f.default||''}</textarea>`;
    } else if (f.type === 'select') {
      const opts = f.options.map(o => {
        const val = typeof o === 'object' ? o.value : o;
        const lbl = typeof o === 'object' ? o.label : o;
        const sel = val === f.default ? 'selected' : '';
        return `<option value="${val}" ${sel}>${lbl}</option>`;
      }).join('');
      inner = `<select class="form-control" id="modal-${f.id}">${opts}</select>`;
    } else if (f.type === 'radio') {
      const btns = f.options.map((o, idx) => {
        const val = typeof o === 'object' ? o.value : o;
        const lbl = typeof o === 'object' ? o.label : o;
        const checked = (f.default ? val === f.default : idx === 0) ? 'checked' : '';
        const sel    = (f.default ? val === f.default : idx === 0) ? 'selected' : '';
        return `<label class="radio-btn ${sel}"><input type="radio" name="${f.id}" value="${val}" ${checked}>${lbl}</label>`;
      }).join('');
      inner = `<div class="radio-group">${btns}</div>`;
    } else if (f.type === 'file') {
      inner = `
        <div class="file-upload-area" onclick="document.getElementById('modal-${f.id}').click()">
          <input type="file" id="modal-${f.id}" accept="${f.accept||'*'}">
          <i data-lucide="upload-cloud" style="width:24px;height:24px;color:var(--muted)"></i>
          <div class="file-label" style="font-size:13px;color:var(--muted);margin-top:6px">${f.placeholder||'파일을 클릭하여 선택'}</div>
          <img class="file-preview" src="" style="display:none">
        </div>`;
    } else {
      inner = `<input class="form-control" id="modal-${f.id}" type="${f.type||'text'}"
        placeholder="${f.placeholder||''}" value="${f.default||''}"
        ${f.min !== undefined ? 'min="'+f.min+'"' : ''}
        ${f.max !== undefined ? 'max="'+f.max+'"' : ''}>`;
    }

    return `<div class="form-group"><label class="form-label">${f.label}${req}</label>${inner}${hint}</div>`;
  }

  window.closeModal = function () {
    const el = document.getElementById('modal-overlay');
    if (el) el.remove();
  };

  // ── Render Shell ──────────────────────────────────────────────
  function renderShell() {
    const root = document.getElementById('app-root');

    const navItemsHTML = Object.entries(PAGES).map(([key, cfg]) => {
      if (cfg.staffOnly && user.role !== 'staff') return '';
      return `
        <div class="nav-item ${key === currentPage ? 'active' : ''}" onclick="navigateTo('${key}')">
          <i data-lucide="${cfg.icon}" class="nav-icon"></i>
          <span>${cfg.label}</span>
        </div>`;
    }).join('');

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
            <img src="/static/img/logo.png" alt="LAONSPORTS" style="height:36px;object-fit:contain;">
            <span class="brand-sub" style="font-size:14px;font-weight:700;margin-left:4px">${user.branch || '지점 포털'}</span>
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
          <div class="page"><div class="empty">로딩 중…</div></div>
        </main>

        <nav class="bottom-tabs">${tabsHTML}</nav>
      </div>
    `;

    if (window.lucide) lucide.createIcons();
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
      default:            container.innerHTML = '<div class="page"><div class="empty">페이지 없음</div></div>';
    }
    if (window.lucide) lucide.createIcons();
  }

  // ── Home ──────────────────────────────────────────────────────
  async function renderHome(container) {
    container.innerHTML = '<div class="page"><div class="empty">홈 로딩 중…</div></div>';
    try {
      const resp = await api('/api/home/data');
      if (!resp) return;
      const data = await resp.json();
      const { announcements = [], events = [], classes = [] } = data;

      const marqueeText = announcements.length
        ? announcements.map(a => a.title).join('    ·    ')
        : '라온스포츠 포털에 오신 것을 환영합니다';

      const ev = events[0];
      const heroHTML = ev ? `
        <div class="hero-main" style="${ev.image_path ? 'background-image:url('+ev.image_path+')' : 'background:#1a1410'}">
          ${ev.eyebrow ? `<div class="eyebrow"><i data-lucide="zap" style="width:12px;height:12px"></i> ${ev.eyebrow}</div>` : ''}
          <h2>${ev.title}</h2>
          <p>${ev.sub || ev.content || ''}</p>
          <button class="btn primary sm" onclick="openEvent(${ev.id})">자세히 보기 →</button>
        </div>` : `
        <div class="hero-main" style="background:#1a1410">
          <h2>라온스포츠에 오신 것을 환영합니다</h2>
          <p>최신 이벤트와 프로그램을 확인해 보세요.</p>
        </div>`;

      const sideEvs = events.slice(1, 3);
      const sideHTML = sideEvs.map(ev => `
        <div class="hero-side-card" style="cursor:pointer" onclick="openEvent(${ev.id})">
          <div class="deadline"><i data-lucide="calendar" style="width:12px;height:12px"></i> ${ev.ends_at || ''}</div>
          <h3>${ev.title}</h3>
          <p class="muted" style="font-size:13px;margin-top:4px">${(ev.sub || ev.content || '').slice(0, 60)}</p>
        </div>`).join('') || '<div class="hero-side-card"><p class="muted">진행중인 이벤트가 없습니다</p></div><div class="hero-side-card dark"><p>새 이벤트를 기대해 주세요</p></div>';

      const classHTML = classes.map(c => `
        <div class="class-card">
          <div class="thumb" style="background:linear-gradient(135deg,#E0382B22,#1a141022)">
            <div class="corner"><span class="badge red">${c.days || '매일'}</span></div>
          </div>
          <div class="meta">
            <div class="title">${c.class_name}</div>
            <div class="row"><i data-lucide="clock" style="width:13px;height:13px"></i><span>${c.start_time} ~ ${c.end_time}</span></div>
            <div class="row"><i data-lucide="user" style="width:13px;height:13px"></i><span>${c.instructor_name || '-'}</span></div>
          </div>
        </div>`).join('') || '<div class="empty">등록된 수업이 없습니다</div>';

      container.innerHTML = `
        <div class="page">
          <div class="marquee"><div class="marquee-wrap"><div class="marquee-track">${marqueeText + '    ·    ' + marqueeText}</div></div></div>
          <div class="hero-grid">${heroHTML}<div class="hero-side">${sideHTML}</div></div>
          <div style="margin-top:28px">
            <div class="card-head">
              <div><div class="section-title">오늘의 수업</div><div class="section-sub">현재 운영 중인 GX 프로그램</div></div>
            </div>
            <div class="class-grid">${classHTML}</div>
          </div>
        </div>`;
    } catch (err) {
      container.innerHTML = `<div class="page"><div class="empty">홈 데이터를 불러올 수 없습니다</div></div>`;
    }
    if (window.lucide) lucide.createIcons();
  }

  window.openEvent = function (id) { showToast('이벤트 상세보기 준비 중'); };

  // ── Attendance ────────────────────────────────────────────────
  async function renderAttendance(container) {
    if (user.role !== 'staff') {
      container.innerHTML = '<div class="page"><div class="empty">직원 전용 메뉴입니다</div></div>'; return;
    }
    container.innerHTML = '<div class="page"><div class="empty">근태 로딩 중…</div></div>';
    try {
      const today = new Date().toISOString().slice(0, 10);
      const resp  = await api('/api/attendance/today');
      if (!resp) return;
      const record = await resp.json();

      const clockInBtn  = record.clock_in
        ? `<button class="btn" disabled style="opacity:.6"><i data-lucide="check"></i> 출근 완료 ${record.clock_in}</button>`
        : `<button class="btn primary" onclick="clockIn()"><i data-lucide="log-in"></i> 출근</button>`;
      const clockOutBtn = record.clock_in && !record.clock_out
        ? `<button class="btn ink" onclick="clockOut()"><i data-lucide="log-out"></i> 퇴근</button>` : '';
      const workMin = record.work_minutes || 0;
      const workHr  = Math.floor(workMin / 60);
      const workRem = workMin % 60;

      container.innerHTML = `
        <div class="page">
          <div class="section-title">근태 관리</div>
          <div class="section-sub">오늘 ${today} · ${user.name}</div>

          <div class="grid-2" style="margin:16px 0 20px;max-width:560px">
            <div class="stat">
              <div class="label">출근 시간</div>
              <div class="value" style="font-size:26px;font-weight:700">${record.clock_in || '—'}</div>
            </div>
            <div class="stat">
              <div class="label">퇴근 시간</div>
              <div class="value" style="font-size:26px;font-weight:700">${record.clock_out || '—'}</div>
            </div>
            <div class="stat">
              <div class="label">근무 시간</div>
              <div class="value">${workMin ? workHr + '시간 ' + workRem + '분' : '—'}</div>
            </div>
            <div class="stat">
              <div class="label">상태</div>
              <div class="value">
                ${record.status ? `<span class="badge ${record.status === 'late' ? 'warn' : 'ok'}">${record.status === 'late' ? '지각' : '정상'}</span>` : '<span class="badge outline">미기록</span>'}
              </div>
            </div>
          </div>

          <div style="display:flex;gap:10px;margin-bottom:28px">
            ${clockInBtn}${clockOutBtn}
          </div>

          <div class="card">
            <div class="card-head" style="padding:16px 20px 0">
              <div class="card-title">이번 달 근태 기록</div>
            </div>
            <div id="monthlyAttendance" style="padding:0 20px 16px"><div class="empty">불러오는 중…</div></div>
          </div>
        </div>`;
      if (window.lucide) lucide.createIcons();
      loadMonthlyAttendance();
    } catch (err) {
      container.innerHTML = `<div class="page"><div class="empty">오류: ${err.message}</div></div>`;
    }
  }

  async function loadMonthlyAttendance() {
    const now  = new Date();
    const resp = await api(`/api/attendance/monthly?year=${now.getFullYear()}&month=${now.getMonth()+1}`);
    if (!resp) return;
    const records = await resp.json();
    const el = document.getElementById('monthlyAttendance');
    if (!el) return;
    if (!records.length) { el.innerHTML = '<div class="empty">이번 달 근태 기록이 없습니다</div>'; return; }
    el.innerHTML = `
      <table class="table">
        <thead><tr><th>날짜</th><th>출근</th><th>퇴근</th><th>근무</th><th>상태</th></tr></thead>
        <tbody>
          ${records.map(r => {
            const m = r.work_minutes || 0;
            const h = Math.floor(m/60), rm = m%60;
            return `<tr>
              <td>${r.work_date}</td>
              <td>${r.clock_in || '—'}</td>
              <td>${r.clock_out || '—'}</td>
              <td>${m ? h+'h '+rm+'m' : '—'}</td>
              <td><span class="badge ${r.status === 'late' ? 'warn' : 'ok'}">${r.status === 'late' ? '지각' : '정상'}</span></td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>`;
  }

  window.clockIn = async function () {
    const time = new Date().toTimeString().slice(0, 5);
    const resp = await api('/api/attendance/clock-in', { method:'POST', body: JSON.stringify({ time }) });
    if (resp && resp.ok) { showToast('출근 처리 완료 — ' + time); navigateTo('attendance'); }
    else { const d = await resp?.json(); showToast(d?.detail || '오류', 'err'); }
  };
  window.clockOut = async function () {
    const time = new Date().toTimeString().slice(0, 5);
    const resp = await api('/api/attendance/clock-out', { method:'POST', body: JSON.stringify({ time }) });
    if (resp && resp.ok) { showToast('퇴근 처리 완료 — ' + time); navigateTo('attendance'); }
    else { const d = await resp?.json(); showToast(d?.detail || '오류', 'err'); }
  };

  // ── Operations ────────────────────────────────────────────────
  async function renderOperations(container) {
    if (user.role !== 'staff') {
      container.innerHTML = '<div class="page"><div class="empty">직원 전용 메뉴입니다</div></div>'; return;
    }
    container.innerHTML = `
      <div class="page">
        <div class="section-title">운영 관리</div>
        <div class="section-sub">재고 · 비품요청 · A/S · 이벤트 · 공지</div>
        <div class="tabs line" style="margin-bottom:22px" id="opsTabs">
          <button class="on" onclick="showOpsTab('inventory',this)">재고</button>
          <button onclick="showOpsTab('supply',this)">비품 요청</button>
          <button onclick="showOpsTab('as',this)">A/S</button>
          <button onclick="showOpsTab('events',this)">이벤트</button>
          <button onclick="showOpsTab('announcements',this)">공지사항</button>
          <button onclick="showOpsTab('instructorsMgmt',this)">강사 관리</button>
        </div>
        <div id="opsContent"><div class="empty">불러오는 중…</div></div>
      </div>`;
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
        const resp  = await api(`/api/operations/inventory?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">재고 목록</div>
            <button class="btn primary sm" onclick="modalAddInventory()"><i data-lucide="plus"></i> 품목 추가</button>
          </div>
          <table class="table">
            <thead><tr><th>품목</th><th>분류</th><th>수량</th><th>최소수량</th><th>단위</th><th>조작</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td><b>${i.item_name}</b></td><td>${i.category}</td>
                  <td style="font-size:16px;font-weight:700;color:${i.quantity<=i.min_quantity?'var(--accent)':'inherit'}">${i.quantity}</td>
                  <td>${i.min_quantity}</td><td>${i.unit}</td>
                  <td>
                    <button class="btn sm" onclick="modalAdjustInventory(${i.id},'in','${i.item_name}')">입고</button>
                    <button class="btn sm" onclick="modalAdjustInventory(${i.id},'out','${i.item_name}')">출고</button>
                  </td>
                </tr>`).join('') || '<tr><td colspan="6" style="text-align:center;color:var(--muted)">재고 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();

      } else if (tab === 'supply') {
        const resp  = await api(`/api/operations/supply?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        const statusLabel = { pending:'대기', approved:'승인', rejected:'반려', delivered:'수령완료' };
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">비품 요청</div>
            <button class="btn primary sm" onclick="modalNewSupply()"><i data-lucide="plus"></i> 요청 등록</button>
          </div>
          <table class="table">
            <thead><tr><th>품목</th><th>수량</th><th>사유</th><th>상태</th><th>요청일</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td><b>${i.item_name}</b></td>
                  <td>${i.quantity} ${i.unit}</td>
                  <td style="color:var(--muted);font-size:13px">${i.reason||'—'}</td>
                  <td><span class="badge ${i.status==='approved'||i.status==='delivered'?'ok':i.status==='rejected'?'red':'warn'}">${statusLabel[i.status]||i.status}</span></td>
                  <td>${i.created_at?i.created_at.slice(0,10):''}</td>
                </tr>`).join('') || '<tr><td colspan="5" style="text-align:center;color:var(--muted)">요청 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();

      } else if (tab === 'as') {
        const resp  = await api(`/api/operations/as?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        const prioLabel = { urgent:'긴급', normal:'일반', low:'낮음' };
        const statLabel = { open:'접수', in_progress:'처리중', done:'완료' };
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">A/S 요청</div>
            <button class="btn primary sm" onclick="modalNewAs()"><i data-lucide="plus"></i> A/S 접수</button>
          </div>
          <table class="table">
            <thead><tr><th>제목</th><th>설명</th><th>우선순위</th><th>상태</th><th>등록일</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td><b>${i.title}</b></td>
                  <td style="color:var(--muted);font-size:13px">${(i.description||'').slice(0,40)}</td>
                  <td><span class="badge ${i.priority==='urgent'?'red':i.priority==='low'?'outline':'warn'}">${prioLabel[i.priority]||i.priority}</span></td>
                  <td><span class="badge ${i.status==='done'?'ok':i.status==='in_progress'?'warn':'outline'}">${statLabel[i.status]||i.status}</span></td>
                  <td>${i.created_at?i.created_at.slice(0,10):''}</td>
                </tr>`).join('') || '<tr><td colspan="5" style="text-align:center;color:var(--muted)">요청 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();

      } else if (tab === 'events') {
        const resp  = await api(`/api/operations/events?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">이벤트 관리</div>
            <button class="btn primary sm" onclick="modalNewEvent()"><i data-lucide="plus"></i> 이벤트 추가</button>
          </div>
          <table class="table">
            <thead><tr><th>제목</th><th>태그</th><th>마감일</th><th>활성</th><th>등록일</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td><b>${i.title}</b></td>
                  <td><span class="badge outline">${i.eyebrow||'—'}</span></td>
                  <td>${i.ends_at||'—'}</td>
                  <td><span class="badge ${i.is_active?'ok':'outline'}">${i.is_active?'활성':'비활성'}</span></td>
                  <td>${i.created_at?i.created_at.slice(0,10):''}</td>
                </tr>`).join('') || '<tr><td colspan="5" style="text-align:center;color:var(--muted)">이벤트 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();

      } else if (tab === 'announcements') {
        const resp  = await api(`/api/operations/announcements?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">공지사항</div>
            <button class="btn primary sm" onclick="modalNewAnnouncement()"><i data-lucide="plus"></i> 공지 등록</button>
          </div>
          <table class="table">
            <thead><tr><th>제목</th><th>내용</th><th>우선순위</th><th>대상</th><th>만료일</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td><b>${i.title}</b></td>
                  <td style="color:var(--muted);font-size:13px">${(i.content||'').slice(0,40)}</td>
                  <td><span class="badge ${i.priority==='urgent'?'red':'outline'}">${i.priority==='urgent'?'긴급':'일반'}</span></td>
                  <td>${i.target_branch==='all'?'전체':i.target_branch}</td>
                  <td>${i.expires_at||'—'}</td>
                </tr>`).join('') || '<tr><td colspan="5" style="text-align:center;color:var(--muted)">공지 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();

      } else if (tab === 'instructorsMgmt') {
        const resp  = await api(`/api/operations/instructors?branch=${encodeURIComponent(branch)}`);
        const items = await resp.json();
        content.innerHTML = `
          <div class="card-head">
            <div class="card-title">강사 관리</div>
            <button class="btn primary sm" onclick="modalNewInstructor()"><i data-lucide="plus"></i> 강사 추가</button>
          </div>
          <table class="table">
            <thead><tr><th>이름</th><th>영문</th><th>역할</th><th>소개</th></tr></thead>
            <tbody>
              ${items.map(i => `
                <tr>
                  <td><b>${i.name}</b></td>
                  <td style="color:var(--muted)">${i.english||'—'}</td>
                  <td><span class="badge outline">${i.role||'—'}</span></td>
                  <td style="color:var(--muted);font-size:13px">${(i.bio||'').slice(0,50)}</td>
                </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;color:var(--muted)">강사 없음</td></tr>'}
            </tbody>
          </table>`;
        if (window.lucide) lucide.createIcons();
      }
    } catch (err) {
      content.innerHTML = `<div class="empty">오류: ${err.message}</div>`;
    }
  };

  // ── Operations Modal Forms ────────────────────────────────────
  window.modalAddInventory = function () {
    createModal({
      title: '재고 품목 추가',
      fields: [
        { id:'item_name', label:'품목명', type:'text', required:true, placeholder:'예: 운동 매트' },
        { id:'category',  label:'분류',   type:'select',
          options:[{value:'일반',label:'일반'},{value:'운동기구',label:'운동기구'},
                   {value:'소모품',label:'소모품'},{value:'청소용품',label:'청소용품'},{value:'사무용품',label:'사무용품'}] },
        { id:'quantity',     label:'초기 수량',  type:'number', default:'0',  min:0, row:'qty' },
        { id:'min_quantity', label:'최소 수량',  type:'number', default:'0',  min:0, row:'qty' },
        { id:'unit', label:'단위', type:'text', default:'개', placeholder:'개 / 롤 / 박스' },
      ],
      submitLabel: '추가',
      onSubmit: async (data) => {
        const resp = await api('/api/operations/inventory', {
          method: 'POST',
          body: JSON.stringify({ ...data, branch: user.branch,
            quantity: parseInt(data.quantity)||0, min_quantity: parseInt(data.min_quantity)||0 })
        });
        if (!resp?.ok) throw new Error('추가 실패');
        showToast('품목이 추가되었습니다');
        showOpsTab('inventory');
      }
    });
  };

  window.modalAdjustInventory = function (id, type, name) {
    createModal({
      title: (type === 'in' ? '📥 입고' : '📤 출고') + ' — ' + name,
      fields: [
        { id:'qty',  label:'수량', type:'number', default:'1', min:1, required:true },
        { id:'note', label:'메모', type:'text', placeholder:'선택사항' },
      ],
      submitLabel: type === 'in' ? '입고 처리' : '출고 처리',
      onSubmit: async (data) => {
        const resp = await api(`/api/operations/inventory/${id}/adjust`, {
          method: 'POST',
          body: JSON.stringify({ type, qty: parseInt(data.qty)||1, note: data.note })
        });
        if (!resp?.ok) throw new Error('처리 실패');
        showToast(type === 'in' ? '입고 처리 완료' : '출고 처리 완료');
        showOpsTab('inventory');
      }
    });
  };

  window.modalNewSupply = function () {
    createModal({
      title: '비품 요청 등록',
      fields: [
        { id:'item_name', label:'품목명', type:'text', required:true, placeholder:'필요한 품목을 입력하세요' },
        { id:'quantity',  label:'수량',   type:'number', default:'1', min:1, row:'qu' },
        { id:'unit',      label:'단위',   type:'text',   default:'개', row:'qu' },
        { id:'reason', label:'요청 사유', type:'textarea', placeholder:'필요한 이유를 간략히 적어주세요' },
      ],
      submitLabel: '요청 등록',
      onSubmit: async (data) => {
        const resp = await api('/api/operations/supply', {
          method: 'POST',
          body: JSON.stringify({ ...data, branch: user.branch, created_name: user.name,
            quantity: parseInt(data.quantity)||1 })
        });
        if (!resp?.ok) throw new Error('등록 실패');
        showToast('비품 요청이 접수되었습니다');
        showOpsTab('supply');
      }
    });
  };

  window.modalNewAs = function () {
    createModal({
      title: 'A/S 요청 접수',
      fields: [
        { id:'title', label:'요청 제목', type:'text', required:true, placeholder:'예: 러닝머신 3번 오작동' },
        { id:'priority', label:'우선순위', type:'radio',
          options:[{value:'urgent',label:'🔴 긴급'},{value:'normal',label:'🟡 일반'},{value:'low',label:'🟢 낮음'}],
          default:'normal' },
        { id:'description', label:'상세 내용', type:'textarea', rows:4,
          placeholder:'증상, 위치, 발생 시점 등을 자세히 적어주세요' },
      ],
      submitLabel: 'A/S 접수',
      onSubmit: async (data) => {
        const resp = await api('/api/operations/as', {
          method: 'POST',
          body: JSON.stringify({ ...data, branch: user.branch, created_name: user.name })
        });
        if (!resp?.ok) throw new Error('접수 실패');
        showToast('A/S 요청이 접수되었습니다');
        showOpsTab('as');
      }
    });
  };

  window.modalNewEvent = function () {
    createModal({
      title: '이벤트 추가',
      size: 'lg',
      fields: [
        { id:'title',   label:'이벤트 제목', type:'text', required:true, placeholder:'예: 여름 특별 GX 이벤트' },
        { id:'eyebrow', label:'태그 (상단 라벨)', type:'text', placeholder:'예: 이벤트 / 프로모션' },
        { id:'content', label:'내용', type:'textarea', rows:4, placeholder:'이벤트 상세 내용을 입력하세요' },
        { id:'ends_at', label:'마감일', type:'date' },
        { id:'image',   label:'이미지', type:'file', accept:'image/*', placeholder:'이미지를 클릭하여 선택 (선택사항)' },
      ],
      submitLabel: '이벤트 등록',
      onSubmit: async (data, hasFile) => {
        const fd = new FormData();
        fd.append('title',   data.title);
        fd.append('eyebrow', data.eyebrow || '');
        fd.append('content', data.content || '');
        fd.append('ends_at', data.ends_at || '');
        fd.append('branch',  user.branch || '');
        if (data.image) fd.append('image', data.image);
        const resp = await apiForm('/api/operations/events', fd);
        if (!resp?.ok) throw new Error('등록 실패');
        showToast('이벤트가 등록되었습니다');
        showOpsTab('events');
      }
    });
  };

  window.modalNewAnnouncement = function () {
    createModal({
      title: '공지사항 등록',
      fields: [
        { id:'title',   label:'제목', type:'text', required:true, placeholder:'공지 제목을 입력하세요' },
        { id:'content', label:'내용', type:'textarea', rows:4, placeholder:'공지 내용을 입력하세요' },
        { id:'priority', label:'우선순위', type:'radio',
          options:[{value:'normal',label:'일반'},{value:'urgent',label:'🔴 긴급'}], default:'normal' },
        { id:'target_branch', label:'대상 지점', type:'text',
          default: user.branch || 'all', placeholder:'all = 전체, 특정 지점명 입력 가능' },
        { id:'expires_at', label:'만료일 (선택)', type:'date' },
      ],
      submitLabel: '공지 등록',
      onSubmit: async (data) => {
        const resp = await api('/api/operations/announcements', {
          method: 'POST',
          body: JSON.stringify({ ...data, created_by: user.name })
        });
        if (!resp?.ok) throw new Error('등록 실패');
        showToast('공지사항이 등록되었습니다');
        showOpsTab('announcements');
      }
    });
  };

  window.modalNewInstructor = function () {
    createModal({
      title: '강사 추가',
      size: 'lg',
      fields: [
        { id:'name',    label:'이름',   type:'text', required:true, placeholder:'강사 이름', row:'nm' },
        { id:'english', label:'영문명', type:'text', placeholder:'English Name', row:'nm' },
        { id:'role',    label:'역할',   type:'text', placeholder:'예: GX강사 / 퍼스널트레이너', row:'rl' },
        { id:'branch',  label:'지점',   type:'text', default: user.branch, row:'rl' },
        { id:'bio',     label:'소개',   type:'textarea', rows:3, placeholder:'강사 소개를 입력하세요' },
        { id:'photo',   label:'프로필 사진', type:'file', accept:'image/*', placeholder:'사진을 클릭하여 선택 (선택사항)' },
      ],
      submitLabel: '강사 추가',
      onSubmit: async (data) => {
        const fd = new FormData();
        ['name','english','role','branch','bio'].forEach(k => fd.append(k, data[k]||''));
        if (data.photo) fd.append('photo', data.photo);
        const resp = await apiForm('/api/operations/instructors', fd);
        if (!resp?.ok) throw new Error('추가 실패');
        showToast('강사가 등록되었습니다');
        showOpsTab('instructorsMgmt');
      }
    });
  };

  // ── Members ───────────────────────────────────────────────────
  async function renderMembers(container) {
    if (user.role !== 'staff') {
      container.innerHTML = '<div class="page"><div class="empty">직원 전용 메뉴입니다</div></div>'; return;
    }
    container.innerHTML = `
      <div class="page">
        <div class="card-head">
          <div><div class="section-title">회원 관리</div><div class="section-sub">${user.branch}</div></div>
          <button class="btn primary" onclick="modalNewMember()"><i data-lucide="user-plus"></i> 신규 등록</button>
        </div>
        <div style="margin-bottom:14px">
          <input class="input" id="memberSearch" placeholder="이름 또는 전화번호 검색…" style="max-width:300px"
                 oninput="searchMembers(this.value)">
        </div>
        <div id="memberList"><div class="empty">불러오는 중…</div></div>
      </div>`;
    if (window.lucide) lucide.createIcons();
    loadMembers('');
  }

  async function loadMembers(q) {
    const branch = user.branch || '';
    const resp   = await api(`/api/members?branch=${encodeURIComponent(branch)}&q=${encodeURIComponent(q)}`);
    if (!resp) return;
    const members = await resp.json();
    const el = document.getElementById('memberList');
    if (!el) return;
    el.innerHTML = `
      <table class="table">
        <thead><tr><th>이름</th><th>전화번호</th><th>이메일</th><th>가입일</th><th>상태</th></tr></thead>
        <tbody>
          ${members.map(m => `
            <tr class="row-hover" style="cursor:pointer" onclick="modalViewMember(${m.id},'${(m.name||'').replace(/'/g,"\\'")}','${m.phone||''}','${m.email||''}','${m.join_date||''}','${m.status||'active'}','${m.note||''}')">
              <td><b>${m.name}</b></td>
              <td>${m.phone || '—'}</td>
              <td style="color:var(--muted);font-size:13px">${m.email || '—'}</td>
              <td>${m.join_date || '—'}</td>
              <td><span class="badge ${m.status==='active'?'ok':'outline'}">${m.status==='active'?'활성':'비활성'}</span></td>
            </tr>`).join('') || '<tr><td colspan="5" style="text-align:center;color:var(--muted)">회원 없음</td></tr>'}
        </tbody>
      </table>`;
  }

  window.searchMembers = function (q) { loadMembers(q); };

  window.modalNewMember = function () {
    createModal({
      title: '회원 신규 등록',
      size: 'lg',
      fields: [
        { id:'name',       label:'이름',     type:'text',   required:true, placeholder:'회원 이름', row:'nm' },
        { id:'phone',      label:'전화번호', type:'text',   placeholder:'010-0000-0000', row:'nm' },
        { id:'email',      label:'이메일',   type:'text',   placeholder:'example@email.com', row:'em' },
        { id:'birth_date', label:'생년월일', type:'date',   row:'em' },
        { id:'gender',     label:'성별',     type:'select',
          options:[{value:'',label:'선택 안함'},{value:'남',label:'남성'},{value:'여',label:'여성'}], row:'gj' },
        { id:'join_date',  label:'가입일',   type:'date',   row:'gj' },
        { id:'note',       label:'메모',     type:'textarea', rows:2, placeholder:'선택사항' },
      ],
      submitLabel: '회원 등록',
      onSubmit: async (data) => {
        const resp = await api('/api/members', {
          method: 'POST',
          body: JSON.stringify({ ...data, branch: user.branch, status: 'active' })
        });
        if (!resp?.ok) throw new Error('등록 실패');
        showToast('회원이 등록되었습니다');
        loadMembers('');
      }
    });
  };

  window.modalViewMember = function (id, name, phone, email, joinDate, status, note) {
    createModal({
      title: '회원 정보 — ' + name,
      fields: [
        { id:'name',      label:'이름',     type:'text',   default: name },
        { id:'phone',     label:'전화번호', type:'text',   default: phone },
        { id:'email',     label:'이메일',   type:'text',   default: email, row:'em' },
        { id:'join_date', label:'가입일',   type:'date',   default: joinDate, row:'em' },
        { id:'status',    label:'상태',     type:'select',
          options:[{value:'active',label:'활성'},{value:'inactive',label:'비활성'}], default: status },
        { id:'note',      label:'메모',     type:'textarea', rows:2, default: note },
        { id:'_id',       label:'',         type:'hidden',  value: String(id) },
      ],
      submitLabel: '저장',
      onSubmit: async (data) => {
        const resp = await api(`/api/members/${id}`, {
          method: 'PATCH',
          body: JSON.stringify({ name: data.name, phone: data.phone, email: data.email,
            join_date: data.join_date, status: data.status, note: data.note })
        });
        if (!resp?.ok) throw new Error('저장 실패');
        showToast('회원 정보가 수정되었습니다');
        loadMembers('');
      }
    });
  };

  // ── Classes ───────────────────────────────────────────────────
  async function renderClasses(container) {
    container.innerHTML = '<div class="page"><div class="empty">수업 로딩 중…</div></div>';
    try {
      const branch = user.branch || '';
      const resp   = await api(`/api/classes?branch=${encodeURIComponent(branch)}`);
      if (!resp) return;
      const classes = await resp.json();
      const addBtn  = user.role === 'staff'
        ? `<button class="btn primary sm" onclick="modalNewClass()"><i data-lucide="plus"></i> 수업 추가</button>` : '';
      container.innerHTML = `
        <div class="page">
          <div class="card-head">
            <div><div class="section-title">수업 시간표</div><div class="section-sub">${branch} · 현재 운영 중인 프로그램</div></div>
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
                  <div class="row"><i data-lucide="clock" style="width:13px;height:13px"></i><span>${c.start_time} ~ ${c.end_time}</span></div>
                  <div class="row"><i data-lucide="user" style="width:13px;height:13px"></i><span>${c.instructor_name || '강사 미배정'}</span></div>
                  <div class="row"><i data-lucide="users" style="width:13px;height:13px"></i><span>정원 ${c.capacity}명</span></div>
                </div>
              </div>`).join('') || '<div class="empty" style="grid-column:1/-1">등록된 수업이 없습니다</div>'}
          </div>
        </div>`;
      if (window.lucide) lucide.createIcons();
    } catch (err) {
      container.innerHTML = `<div class="page"><div class="empty">오류: ${err.message}</div></div>`;
    }
  }

  window.modalNewClass = function () {
    createModal({
      title: '수업 추가',
      size: 'lg',
      fields: [
        { id:'class_name',      label:'수업 이름',  type:'text', required:true, placeholder:'예: 줌바댄스 / 필라테스' },
        { id:'instructor_name', label:'담당 강사',  type:'text', placeholder:'강사 이름' },
        { id:'days',       label:'운영 요일',   type:'text', placeholder:'예: 월수금 / 화목 / 매일', row:'dt' },
        { id:'capacity',   label:'정원 (명)',   type:'number', default:'20', min:1, row:'dt' },
        { id:'start_time', label:'시작 시간',   type:'time', default:'10:00', row:'tm' },
        { id:'end_time',   label:'종료 시간',   type:'time', default:'11:00', row:'tm' },
      ],
      submitLabel: '수업 등록',
      onSubmit: async (data) => {
        const resp = await api('/api/classes', {
          method: 'POST',
          body: JSON.stringify({ ...data, branch: user.branch, capacity: parseInt(data.capacity)||20 })
        });
        if (!resp?.ok) throw new Error('등록 실패');
        showToast('수업이 등록되었습니다');
        renderClasses(document.getElementById('page-content'));
      }
    });
  };

  // ── Instructors ───────────────────────────────────────────────
  async function renderInstructors(container) {
    container.innerHTML = '<div class="page"><div class="empty">강사 로딩 중…</div></div>';
    try {
      const branch     = user.branch || '';
      const resp       = await api(`/api/operations/instructors?branch=${encodeURIComponent(branch)}`);
      if (!resp) return;
      const instructors = await resp.json();
      const addBtn = user.role === 'staff'
        ? `<button class="btn primary sm" onclick="modalNewInstructor()"><i data-lucide="plus"></i> 강사 추가</button>` : '';
      container.innerHTML = `
        <div class="page">
          <div class="card-head">
            <div><div class="section-title">강사 소개</div><div class="section-sub">라온스포츠 전문 트레이너</div></div>
            ${addBtn}
          </div>
          <div class="grid-3">
            ${instructors.map(i => `
              <div class="instructor-card">
                <div class="photo" style="${i.photo_path ? 'background-image:url('+i.photo_path+')' : 'background:var(--surface-2)'}">
                  ${!i.photo_path ? `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:48px;color:var(--muted)">${i.name.charAt(0)}</div>` : ''}
                  <div class="name-overlay">
                    <div class="name">${i.name}</div>
                    <div style="font-size:12px;opacity:.8">${i.english || ''}</div>
                  </div>
                </div>
                <div class="body">
                  <span class="badge outline">${i.role || '강사'}</span>
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

  // ── Navigation ────────────────────────────────────────────────
  window.navigateTo = function (page) {
    const cfg = PAGES[page];
    if (!cfg) return;
    if (cfg.staffOnly && user.role !== 'staff') { showToast('직원 전용 메뉴입니다', 'err'); return; }
    currentPage = page;
    history.pushState({ page }, '', '/' + page);
    renderShell();
  };
  window.addEventListener('popstate', e => {
    if (e.state && e.state.page) { currentPage = e.state.page; renderShell(); }
  });

  // ── Toast ─────────────────────────────────────────────────────
  function showToast(msg, type = 'ok') {
    let stack = document.querySelector('.toast-stack');
    if (!stack) { stack = document.createElement('div'); stack.className = 'toast-stack'; document.body.appendChild(stack); }
    const t = document.createElement('div');
    t.className = 'toast';
    t.innerHTML = `<i data-lucide="${type === 'err' ? 'alert-circle' : 'check-circle'}" class="ic"></i> ${msg}`;
    stack.appendChild(t);
    if (window.lucide) lucide.createIcons();
    setTimeout(() => t.remove(), 3500);
  }

  // ── Theme ─────────────────────────────────────────────────────
  window.toggleTheme = function () {
    const html  = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('raon_theme', isDark ? 'light' : 'dark');
  };

  // Apply saved theme
  const savedTheme = localStorage.getItem('raon_theme');
  if (savedTheme) document.documentElement.setAttribute('data-theme', savedTheme);

  window.logout = logout;

  // ── Boot ──────────────────────────────────────────────────────
  renderShell();
})();
