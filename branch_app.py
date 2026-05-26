"""
branch_app.py — 라온스포츠 지점 포털 (Phase 1~5)
포트 8502 독립 실행. ERP(8501)와 완전 분리.
PC: 좌측 사이드바 / 모바일: 하단 내비게이션바
"""
import streamlit as st
from datetime import datetime, date

# ── 페이지 설정 ───────────────────────────────────────────────
st.set_page_config(
    page_title="라온스포츠 포털",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: 반응형 사이드바 + 하단 내비 ─────────────────────────
st.markdown("""
<style>
/* ── 전체 기본 ── */
*, *::before, *::after { box-sizing: border-box; }
#MainMenu, footer, header { visibility: hidden !important; }

/* ── 사이드바 스타일 (PC) ── */
[data-testid="stSidebar"] {
    background: #1a1a2e !important;
    min-width: 220px !important;
}
[data-testid="stSidebar"] * { color: #e8e8f0 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.15) !important; }
[data-testid="stSidebarContent"] { padding: 1rem !important; }

/* 사이드바 버튼 */
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    text-align: left !important;
    background: transparent !important;
    border: none !important;
    color: #c8cde8 !important;
    padding: 9px 14px !important;
    border-radius: 8px !important;
    font-size: .92rem !important;
    font-weight: 500 !important;
    transition: background .15s !important;
    cursor: pointer !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,.1) !important;
}
[data-testid="stSidebar"] .nav-active > button {
    background: #c8253c !important;
    color: white !important;
    font-weight: 700 !important;
}

/* ── 모바일 하단 내비 ── */
@media (max-width: 768px) {
    [data-testid="stSidebar"] { display: none !important; }
    .main .block-container { padding-bottom: 76px !important; }
}
@media (min-width: 769px) {
    .bnav-wrap { display: none !important; }
}

.bnav-wrap {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    z-index: 9999;
    background: #fff;
    border-top: 1px solid #e5e5e5;
    display: flex;
    justify-content: space-around;
    align-items: center;
    height: 60px;
    padding-bottom: env(safe-area-inset-bottom, 0px);
    box-shadow: 0 -2px 12px rgba(0,0,0,.08);
}
.bnav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    cursor: pointer;
    text-decoration: none;
    color: #888;
    font-size: .62rem;
    font-weight: 600;
    flex: 1;
    padding: 6px 0;
    transition: color .15s;
    border: none;
    background: transparent;
    outline: none;
    -webkit-tap-highlight-color: transparent;
}
.bnav-item .bnav-icon { font-size: 1.3rem; line-height: 1; }
.bnav-item.active { color: #c8253c; }

/* ── 메인 컨텐츠 ── */
.main .block-container {
    padding: 1.2rem 1.6rem !important;
    max-width: 1200px !important;
}

/* ── 페이지 타이틀 ── */
.page-header {
    display: flex;
    align-items: center;
    gap: .8rem;
    margin-bottom: 1.2rem;
    padding-bottom: .8rem;
    border-bottom: 2px solid #f0f0f0;
}
.page-header .ph-icon { font-size: 1.6rem; }
.page-header .ph-title { font-size: 1.3rem; font-weight: 800; color: #1a1a2e; }
.page-header .ph-branch {
    margin-left: auto;
    font-size: .82rem;
    color: #888;
    background: #f5f5f5;
    padding: 4px 10px;
    border-radius: 20px;
}

/* ── 로그인 카드 ── */
.login-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 90vh;
}
.login-card {
    background: #fff;
    border-radius: 20px;
    padding: 2.5rem 2rem 2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,.12);
    width: 100%;
    max-width: 420px;
}
.login-logo { text-align: center; font-size: 3rem; margin-bottom: .4rem; }
.login-brand {
    text-align: center;
    font-size: 1.7rem;
    font-weight: 900;
    color: #c8253c;
    margin-bottom: .2rem;
    letter-spacing: -.02em;
}
.login-sub { text-align: center; font-size: .85rem; color: #999; margin-bottom: 2rem; }
.login-hint { text-align: center; font-size: .78rem; color: #bbb; margin-top: 1rem; }

/* ── 일반 버튼 ── */
div[data-testid="stButton"] button[kind="primary"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  내비게이션 정의
# ════════════════════════════════════════════════════════════════
NAV = [
    ("home",    "🏠", "홈"),
    ("att",     "📅", "근태"),
    ("ops",     "🔧", "운영"),
    ("members", "👥", "회원"),
    ("pay",     "💳", "결제"),
    ("sms",     "📱", "문자"),
    ("profile", "👤", "내 정보"),
]

# 관리자 전용 메뉴 (Phase 2~5)
ADMIN_PAGES = {"ops","members","pay","sms"}


def _page() -> str:
    return st.session_state.get("_page","home")

def _go(page: str):
    st.session_state["_page"] = page
    st.rerun()

def _current_user() -> dict | None:
    return st.session_state.get("branch_user")


# ════════════════════════════════════════════════════════════════
#  로그인 화면
# ════════════════════════════════════════════════════════════════
def _render_login():
    st.markdown('<div class="login-card" style="margin:4rem auto;">', unsafe_allow_html=True)
    st.markdown('<div class="login-logo">🏋️</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-brand">라온스포츠</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">지점 운영 포털</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("아이디 (이메일)", placeholder="등록된 이메일")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", use_container_width=True, type="primary")

    if submitted:
        if not username or not password:
            st.error("아이디와 비밀번호를 입력하세요.")
        else:
            from domains.payroll.db import verify_employee_login
            u = verify_employee_login(username, password)
            if u:
                st.session_state["branch_user"] = u
                st.session_state["_page"] = "home"
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    st.markdown('<div class="login-hint">비밀번호 분실 시 관리자에게 문의하세요.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  최초 로그인 비밀번호 변경
# ════════════════════════════════════════════════════════════════
def _render_change_pw(user: dict):
    st.markdown(f"## 🔑 비밀번호 변경")
    st.info(f"**{user['name']}**님, 최초 로그인입니다. 보안을 위해 비밀번호를 변경해 주세요.")
    with st.form("force_pw"):
        pw1 = st.text_input("새 비밀번호 (6자 이상)", type="password")
        pw2 = st.text_input("새 비밀번호 확인", type="password")
        if st.form_submit_button("변경하기", type="primary", use_container_width=True):
            if len(pw1) < 6:
                st.error("6자 이상 입력하세요.")
            elif pw1 != pw2:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                from domains.payroll.db import update_employee_password
                update_employee_password(user["employee_id"], pw1)
                st.session_state["branch_user"]["must_change_pw"] = False
                st.success("✅ 변경 완료!")
                st.rerun()


# ════════════════════════════════════════════════════════════════
#  사이드바 (PC 전용)
# ════════════════════════════════════════════════════════════════
def _render_sidebar(user: dict, cur_page: str):
    with st.sidebar:
        # 로고 + 유저 정보
        st.markdown(f"""
        <div style="margin-bottom:1.2rem;">
            <div style="font-size:1.4rem;font-weight:900;color:#fff;letter-spacing:-.02em;">
                🏋️ 라온스포츠
            </div>
            <div style="font-size:.82rem;color:#aab;margin-top:4px;">📍 {user['branch']}</div>
            <div style="font-size:.78rem;color:#889;margin-top:2px;">
                {user['name']} &nbsp;|&nbsp; {datetime.now().strftime('%m/%d %H:%M')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        for pid, icon, label in NAV:
            is_active = (cur_page == pid)
            label_str = f"{icon} {label}"
            if is_active:
                st.markdown(f'<div class="nav-active">', unsafe_allow_html=True)
            if st.button(label_str, key=f"nav_{pid}", use_container_width=True):
                _go(pid)
            if is_active:
                st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        if st.button("🚪 로그아웃", use_container_width=True):
            st.session_state.pop("branch_user", None)
            st.session_state.pop("_page", None)
            st.rerun()


# ════════════════════════════════════════════════════════════════
#  모바일 하단 내비 (JS로 페이지 전환)
# ════════════════════════════════════════════════════════════════
def _render_bottom_nav(cur_page: str):
    # 모바일용 핵심 메뉴 (7개 중 5개)
    mobile_nav = [("home","🏠","홈"), ("att","📅","근태"),
                  ("ops","🔧","운영"), ("members","👥","회원"),
                  ("pay","💳","결제")]

    items_html = ""
    for pid, icon, label in mobile_nav:
        active_cls = "active" if cur_page == pid else ""
        items_html += f"""
        <button class="bnav-item {active_cls}" onclick="window.parent.postMessage({{type:'bnav',page:'{pid}'}},'*')">
            <span class="bnav-icon">{icon}</span>{label}
        </button>"""

    st.markdown(f'<div class="bnav-wrap">{items_html}</div>', unsafe_allow_html=True)

    # JS: 포스트메시지 수신 → Streamlit 상태 업데이트
    st.markdown("""
    <script>
    window.addEventListener('message', function(e) {
        if (e.data && e.data.type === 'bnav') {
            const inputs = window.parent.document.querySelectorAll('input[data-testid="stTextInput"]');
            // Streamlit session_state 접근 불가 → URL query 방식 사용
            const url = new URL(window.parent.location.href);
            url.searchParams.set('nav', e.data.page);
            window.parent.history.replaceState({}, '', url);
            window.parent.location.reload();
        }
    });
    // 초기 로드 시 query param 처리
    (function() {
        const params = new URLSearchParams(window.parent.location.search);
        const nav = params.get('nav');
        if (nav) {
            params.delete('nav');
            const url = window.parent.location.pathname + (params.toString() ? '?' + params.toString() : '');
            window.parent.history.replaceState({}, '', url);
        }
    })();
    </script>
    """, unsafe_allow_html=True)

    # URL query param으로 모바일 네비 처리
    try:
        nav_param = st.query_params.get("nav")
        if nav_param and nav_param != cur_page:
            st.session_state["_page"] = nav_param
            st.query_params.pop("nav", None)
            st.rerun()
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════
#  페이지 헤더
# ════════════════════════════════════════════════════════════════
def _page_header(icon: str, title: str, branch: str):
    st.markdown(f"""
    <div class="page-header">
        <span class="ph-icon">{icon}</span>
        <span class="ph-title">{title}</span>
        <span class="ph-branch">📍 {branch}</span>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  근태현황 페이지 (별도)
# ════════════════════════════════════════════════════════════════
def _render_attendance(user: dict):
    from domains.payroll.db import get_monthly_attendance
    import calendar

    _page_header("📅", "근태현황", user["branch"])
    now   = datetime.now()
    today = date.today()

    c1, c2 = st.columns(2)
    sel_y = c1.selectbox("연도", [now.year, now.year - 1], key="att_yr")
    sel_m = c2.selectbox("월", list(range(1,13)), index=now.month-1,
                          format_func=lambda m: f"{m}월", key="att_mn")

    records = get_monthly_attendance(user["employee_id"], sel_y, sel_m)
    rec_map = {r["work_date"]: r for r in records}

    # 요약
    worked   = sum(1 for r in records if r.get("clock_in"))
    total_m  = sum(r.get("work_minutes",0) for r in records)
    late_cnt = sum(1 for r in records if r.get("status")=="late")
    h, mn    = divmod(total_m, 60)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("근무일", f"{worked}일")
    c2.metric("총 근로", f"{h}h {mn}m")
    c3.metric("지각", f"{late_cnt}회")
    c4.metric("결근", f"{max(0, (today.day if (sel_y==now.year and sel_m==now.month) else calendar.monthrange(sel_y,sel_m)[1]) - worked)}일")

    st.divider()

    # 달력
    _, num_days = calendar.monthrange(sel_y, sel_m)
    first_wd    = date(sel_y, sel_m, 1).weekday()

    st.markdown(f"#### {sel_y}년 {sel_m}월")
    cols_h = st.columns(7)
    for i, d in enumerate(["월","화","수","목","금","토","일"]):
        color = "#c8253c" if i >= 5 else "#555"
        cols_h[i].markdown(f"<div style='text-align:center;font-weight:700;color:{color};font-size:.78rem'>{d}</div>",
                           unsafe_allow_html=True)

    cells: list[str] = [""] * first_wd
    for day in range(1, num_days + 1):
        d_s   = f"{sel_y}-{sel_m:02d}-{day:02d}"
        d_obj = date(sel_y, sel_m, day)
        r     = rec_map.get(d_s)
        is_td = (d_obj == today)
        bd    = "border:2px solid #c8253c;" if is_td else ""

        if d_obj.weekday() >= 5:
            bg, txt = "#f5f5f5", "#bbb"
        elif r and r.get("clock_in"):
            st_  = r.get("status","present")
            bg   = "#c8e6c9" if st_=="present" else "#fff9c4"
            txt  = "#1b5e20" if st_=="present" else "#f57f17"
        elif d_obj < today:
            bg, txt = "#ffcdd2", "#b71c1c"
        else:
            bg, txt = "#f9f9f9", "#ccc"

        tooltip = ""
        if r and r.get("clock_in"):
            tooltip = f"{r.get('clock_in','')}~{r.get('clock_out','')}"

        cells.append(f'<div title="{tooltip}" style="background:{bg};color:{txt};{bd}border-radius:50%;'
                     f'width:34px;height:34px;line-height:34px;text-align:center;'
                     f'font-size:.82rem;font-weight:600;margin:2px auto;">{day}</div>')

    while len(cells) % 7:
        cells.append("")

    for ws in range(0, len(cells), 7):
        cols = st.columns(7)
        for i, cell in enumerate(cells[ws:ws+7]):
            cols[i].markdown(cell, unsafe_allow_html=True)

    # 범례
    st.markdown("""
    <div style='margin-top:.8rem;font-size:.76rem;color:#666;'>
    <span style='background:#c8e6c9;padding:2px 8px;border-radius:10px;margin-right:6px'>정상</span>
    <span style='background:#fff9c4;padding:2px 8px;border-radius:10px;margin-right:6px'>⚠ 지각</span>
    <span style='background:#ffcdd2;padding:2px 8px;border-radius:10px;'>✗ 결근</span>
    </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 상세 내역")
    _WDAY = ["월","화","수","목","금","토","일"]
    import pandas as pd
    rows = []
    for day in range(1, num_days + 1):
        d_s   = f"{sel_y}-{sel_m:02d}-{day:02d}"
        d_obj = date(sel_y, sel_m, day)
        if d_obj.weekday() >= 5:
            continue
        r = rec_map.get(d_s)
        wm = r.get("work_minutes",0) if r else 0
        hh, mm = divmod(wm, 60)
        rows.append({
            "날짜": d_s, "요일": _WDAY[d_obj.weekday()],
            "출근": (r.get("clock_in","-") or "-") if r else "-",
            "퇴근": (r.get("clock_out","-") or "-") if r else "-",
            "근무": f"{hh}h {mm:02d}m" if wm else "-",
            "상태": {"present":"✅","late":"⚠️ 지각","early_leave":"⏰ 조퇴"}.get(r.get("status","") if r else "", ("❌ 결근" if d_obj < today else "—")),
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=350)


# ════════════════════════════════════════════════════════════════
#  내 정보
# ════════════════════════════════════════════════════════════════
def _render_profile(user: dict):
    _page_header("👤", "내 정보", user["branch"])

    p = user.get("phone","").replace("-","").replace(" ","")
    phone_disp = f"***-****-{p[-4:]}" if len(p) >= 4 else (user.get("phone") or "—")

    c1, c2 = st.columns(2)
    c1.markdown(f"**이름** : {user['name']}")
    c2.markdown(f"**소속지점** : {user['branch']}")
    c1.markdown(f"**이메일** : {user.get('email') or '—'}")
    c2.markdown(f"**전화번호** : {phone_disp}")
    c1.markdown(f"**근무시간** : {user.get('work_start','09:00')} ~ {user.get('work_end','18:00')}")

    st.divider()
    st.subheader("🔑 비밀번호 변경")
    with st.form("pw_change"):
        cur = st.text_input("현재 비밀번호", type="password")
        pw1 = st.text_input("새 비밀번호 (6자 이상)", type="password")
        pw2 = st.text_input("새 비밀번호 확인", type="password")
        if st.form_submit_button("변경", type="primary"):
            from domains.payroll.db import verify_employee_login, update_employee_password
            if not verify_employee_login(user["username"], cur):
                st.error("현재 비밀번호가 올바르지 않습니다.")
            elif len(pw1) < 6:
                st.error("6자 이상 입력하세요.")
            elif pw1 != pw2:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                update_employee_password(user["employee_id"], pw1)
                st.success("✅ 변경 완료")

    st.divider()
    if st.button("🚪 로그아웃"):
        st.session_state.pop("branch_user", None)
        st.session_state.pop("_page", None)
        st.rerun()


# ════════════════════════════════════════════════════════════════
#  메인 라우터
# ════════════════════════════════════════════════════════════════
def _main(user: dict):
    cur = _page()

    # 사이드바 (PC)
    _render_sidebar(user, cur)

    # 모바일 하단 내비
    _render_bottom_nav(cur)

    # 컨텐츠
    if cur == "home":
        _page_header("🏠", "홈", user["branch"])
        from domains.branch_app.pages.home import render as _home
        _home(user)

    elif cur == "att":
        _render_attendance(user)

    elif cur == "ops":
        _page_header("🔧", "운영관리", user["branch"])
        from domains.branch_app.pages.operations import render as _ops
        _ops(user)

    elif cur == "members":
        _page_header("👥", "회원관리", user["branch"])
        from domains.branch_app.pages.members import render as _mem
        _mem(user)

    elif cur == "pay":
        _page_header("💳", "결제 / POS", user["branch"])
        from domains.branch_app.pages.payments import render as _pay
        _pay(user)

    elif cur == "sms":
        _page_header("📱", "문자 발송", user["branch"])
        from domains.branch_app.pages.sms import render as _sms
        _sms(user)

    elif cur == "profile":
        _render_profile(user)

    else:
        _go("home")


# ════════════════════════════════════════════════════════════════
#  DB 초기화 + 실행
# ════════════════════════════════════════════════════════════════
@st.cache_resource
def _init_db():
    from domains.payroll.db import init_payroll_tables
    from domains.branch_app.db import init_branch_tables
    init_payroll_tables()
    init_branch_tables()
    return True

_init_db()

# 라우팅
user = _current_user()

if not user:
    _render_login()
elif user.get("must_change_pw"):
    _render_change_pw(user)
else:
    _main(user)
