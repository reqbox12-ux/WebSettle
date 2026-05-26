"""
branch_app.py — 라온스포츠 직원 랜딩페이지
포트 8502에서 독립 실행. ERP(8501)와 완전 분리.
직원: 이메일 + 비밀번호 로그인
회원: 휴대폰 뒷4자리 PIN (Phase 3에서 구현)
"""
import streamlit as st
from datetime import datetime, date, timedelta
import calendar

st.set_page_config(
    page_title="라온스포츠 직원포털",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS (모바일 최적화) ───────────────────────────────────────
st.markdown("""
<style>
/* 전체 레이아웃 */
.main .block-container {
    max-width: 520px !important;
    padding: 1rem 1.2rem 2rem !important;
    margin: 0 auto !important;
}
[data-testid="stSidebar"] { display: none !important; }
#MainMenu, footer, header { visibility: hidden !important; }

/* 헤더 바 */
.header-bar {
    background: linear-gradient(135deg, #c8253c 0%, #8b1a2b 100%);
    color: white;
    padding: 1rem 1.2rem;
    border-radius: 14px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(200,37,60,.25);
}
.header-name { font-size: 1.1rem; font-weight: 700; }
.header-branch { font-size: 0.9rem; opacity: .88; margin-top: 2px; }
.header-date   { font-size: 0.78rem; opacity: .72; margin-top: 3px; }

/* 상태 뱃지 */
.status-badge {
    text-align: center;
    padding: 0.7rem 1rem;
    border-radius: 50px;
    font-size: 1.05rem;
    font-weight: 700;
    margin: 0.8rem 0;
}
.s-before  { background: #f3f3f3; color: #666; }
.s-working { background: #e8f5e9; color: #2e7d32; border: 2px solid #66bb6a; }
.s-done    { background: #e3f2fd; color: #1565c0; border: 2px solid #64b5f6; }

/* 출퇴근 버튼 크게 */
div[data-testid="stButton"] button {
    height: 52px !important;
    font-size: 1.05rem !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    letter-spacing: .02em;
}

/* 출근 버튼 */
div[data-testid="stButton"].clock-in-btn button {
    background: linear-gradient(135deg, #43a047, #1b5e20) !important;
    color: white !important;
}

/* 로그인 카드 */
.login-wrap {
    min-height: 92vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
.login-card {
    background: white;
    border-radius: 20px;
    padding: 2.4rem 2rem 2rem;
    box-shadow: 0 6px 30px rgba(0,0,0,.12);
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
}
.login-logo {
    text-align: center;
    font-size: 3rem;
    margin-bottom: .4rem;
}
.login-brand {
    text-align: center;
    font-size: 1.6rem;
    font-weight: 800;
    color: #c8253c;
    margin-bottom: .2rem;
    letter-spacing: -.02em;
}
.login-sub {
    text-align: center;
    font-size: .85rem;
    color: #888;
    margin-bottom: 1.8rem;
}
.login-hint {
    text-align: center;
    font-size: .8rem;
    color: #aaa;
    margin-top: 1rem;
}

/* 근태 달력 */
.att-day {
    display: inline-block;
    width: 36px; height: 36px;
    line-height: 36px;
    text-align: center;
    border-radius: 50%;
    font-size: .85rem;
    font-weight: 600;
    margin: 2px;
    cursor: default;
}
.att-present  { background: #c8e6c9; color: #1b5e20; }
.att-late     { background: #fff9c4; color: #f57f17; }
.att-absent   { background: #ffcdd2; color: #b71c1c; }
.att-weekend  { background: transparent; color: #bdbdbd; }
.att-future   { background: #f5f5f5; color: #bdbdbd; }
.att-today    { border: 2px solid #c8253c !important; }
.att-header   { font-weight: 700; color: #555; font-size: .78rem; text-align: center; }

/* 요약 카드 */
.sum-card {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
    padding: .8rem;
    text-align: center;
}
.sum-val { font-size: 1.4rem; font-weight: 800; color: #c8253c; }
.sum-lbl { font-size: .78rem; color: #888; margin-top: 2px; }

/* 클락 정보 */
.clock-info {
    text-align: center;
    font-size: .95rem;
    color: #444;
    margin: .5rem 0 1rem;
    padding: .6rem;
    background: #f9f9f9;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# ── 유틸 ─────────────────────────────────────────────────────
_WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

def _wday(d: date) -> str:
    return _WEEKDAY_KR[d.weekday()]

def _fmt_min(m: int) -> str:
    h, mn = divmod(m, 60)
    return f"{h}h {mn:02d}m"

def _elapsed_str(clock_in: str, ref: date) -> str:
    try:
        ci = datetime.strptime(f"{ref} {clock_in}", "%Y-%m-%d %H:%M")
        mins = max(0, int((datetime.now() - ci).total_seconds() / 60))
        return _fmt_min(mins)
    except Exception:
        return "-"


# ── 인증 ─────────────────────────────────────────────────────
def _current_user():
    return st.session_state.get("branch_user")

def _logout():
    st.session_state.pop("branch_user", None)
    st.rerun()


# ── 로그인 화면 ───────────────────────────────────────────────
def _render_login():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-logo">🏋️</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-brand">라온스포츠</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">직원 전용 포털</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("아이디 (이메일)", placeholder="등록된 이메일을 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호")
        submitted = st.form_submit_button("로그인", use_container_width=True, type="primary")

    if submitted:
        if not username or not password:
            st.error("아이디와 비밀번호를 입력하세요.")
        else:
            from domains.payroll.db import verify_employee_login
            user = verify_employee_login(username, password)
            if user:
                st.session_state["branch_user"] = user
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    st.markdown('<div class="login-hint">비밀번호를 잊으셨나요? 관리자에게 문의하세요.</div>',
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ── 비밀번호 변경 강제 (최초 로그인) ─────────────────────────
def _render_change_pw(user: dict):
    st.title("🔑 비밀번호 변경")
    st.info(f"안녕하세요, **{user['name']}**님! 보안을 위해 초기 비밀번호를 변경해 주세요.")

    with st.form("force_change_pw"):
        new_pw  = st.text_input("새 비밀번호 (6자 이상)", type="password")
        new_pw2 = st.text_input("새 비밀번호 확인", type="password")
        if st.form_submit_button("변경하기", type="primary", use_container_width=True):
            if len(new_pw) < 6:
                st.error("비밀번호는 6자 이상이어야 합니다.")
            elif new_pw != new_pw2:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                from domains.payroll.db import update_employee_password
                if update_employee_password(user["employee_id"], new_pw):
                    st.session_state["branch_user"]["must_change_pw"] = False
                    st.success("✅ 비밀번호가 변경되었습니다.")
                    st.rerun()
                else:
                    st.error("변경 실패. 관리자에게 문의하세요.")


# ── 메인 화면 ─────────────────────────────────────────────────
def _render_main(user: dict):
    now = datetime.now()
    today = now.date()

    # 헤더
    st.markdown(f"""
    <div class="header-bar">
        <div class="header-name">안녕하세요, {user['name']}님 👋</div>
        <div class="header-branch">📍 {user['branch']}</div>
        <div class="header-date">{today.strftime('%Y년 %m월 %d일')} ({_wday(today)})</div>
    </div>
    """, unsafe_allow_html=True)

    tab_home, tab_att, tab_profile = st.tabs(["🏠 홈", "📅 근태현황", "👤 내 정보"])

    with tab_home:
        _render_home(user, today, now)
    with tab_att:
        _render_attendance(user)
    with tab_profile:
        _render_profile(user)


# ── 홈 탭 ────────────────────────────────────────────────────
def _render_home(user: dict, today: date, now: datetime):
    from domains.payroll.db import (
        get_attendance_record, attendance_clock_in,
        attendance_clock_out, get_monthly_attendance,
    )

    work_date = today.strftime("%Y-%m-%d")
    now_hm    = now.strftime("%H:%M")
    rec       = get_attendance_record(user["employee_id"], work_date)

    ci = rec.get("clock_in")  if rec else None
    co = rec.get("clock_out") if rec else None

    # ── 출근 전
    if not ci:
        st.markdown('<div class="status-badge s-before">⏳ 출근 전</div>', unsafe_allow_html=True)
        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            if st.button("🟢  출근하기", use_container_width=True, key="btn_ci", type="primary"):
                ok, msg = attendance_clock_in(user["employee_id"], work_date, now_hm)
                if ok:
                    st.success(f"✅ 출근 완료 — {msg}")
                    st.rerun()
                else:
                    st.error(msg)

    # ── 근무 중
    elif ci and not co:
        st.markdown('<div class="status-badge s-working">🟢 근무 중</div>', unsafe_allow_html=True)
        elapsed = _elapsed_str(ci, today)
        st.markdown(f'<div class="clock-info">출근시간 <b>{ci}</b> &nbsp;|&nbsp; 근무시간 <b>{elapsed}</b></div>',
                    unsafe_allow_html=True)
        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            if st.button("🔴  퇴근하기", use_container_width=True, key="btn_co"):
                ok, msg = attendance_clock_out(
                    user["employee_id"], work_date, now_hm,
                    user.get("work_start", "09:00")
                )
                if ok:
                    st.success(f"✅ 퇴근 완료 — {msg}")
                    st.rerun()
                else:
                    st.error(msg)

    # ── 퇴근 완료
    else:
        st.markdown('<div class="status-badge s-done">✅ 퇴근 완료</div>', unsafe_allow_html=True)
        wm = rec.get("work_minutes", 0) if rec else 0
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("출근", ci or "-")
        col_b.metric("퇴근", co or "-")
        col_c.metric("근무시간", _fmt_min(wm))

    # ── 이번달 요약
    st.divider()
    st.markdown("#### 📊 이번달 요약")
    records = get_monthly_attendance(user["employee_id"], today.year, today.month)

    worked_days = len([r for r in records if r.get("work_minutes", 0) > 0 or r.get("clock_in")])
    total_min   = sum(r.get("work_minutes", 0) for r in records)
    late_cnt    = len([r for r in records if r.get("status") == "late"])

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="sum-card"><div class="sum-val">{worked_days}</div><div class="sum-lbl">근무일</div></div>',
                unsafe_allow_html=True)
    c2.markdown(f'<div class="sum-card"><div class="sum-val">{_fmt_min(total_min)}</div><div class="sum-lbl">총 근로시간</div></div>',
                unsafe_allow_html=True)
    c3.markdown(f'<div class="sum-card"><div class="sum-val">{late_cnt}회</div><div class="sum-lbl">지각</div></div>',
                unsafe_allow_html=True)


# ── 근태현황 탭 ───────────────────────────────────────────────
def _render_attendance(user: dict):
    from domains.payroll.db import get_monthly_attendance

    now   = datetime.now()
    today = date.today()

    col1, col2 = st.columns(2)
    sel_year  = col1.selectbox("연도", [now.year, now.year - 1], key="att_yr")
    sel_month = col2.selectbox("월", list(range(1, 13)), index=now.month - 1,
                               format_func=lambda m: f"{m}월", key="att_mn")

    records = get_monthly_attendance(user["employee_id"], sel_year, sel_month)
    rec_map = {r["work_date"]: r for r in records}

    _, num_days = calendar.monthrange(sel_year, sel_month)
    first_wday  = date(sel_year, sel_month, 1).weekday()  # 0=월

    st.markdown(f"#### {sel_year}년 {sel_month}월 근태 현황")

    # 달력 헤더
    days_header = ["월", "화", "수", "목", "금", "토", "일"]
    cols = st.columns(7)
    for i, dh in enumerate(days_header):
        color = "#c8253c" if i >= 5 else "#333"
        cols[i].markdown(f"<div style='text-align:center;font-weight:700;color:{color};font-size:.82rem'>{dh}</div>",
                         unsafe_allow_html=True)

    # 달력 그리드
    cell_idx = first_wday
    cells: list[str] = [""] * first_wday

    STATUS_STYLE = {
        "present":    "att-present",
        "late":       "att-late",
        "early_leave":"att-late",
        "absent":     "att-absent",
    }
    STATUS_EMOJI = {"present": "", "late": "⚠", "early_leave": "⏰", "absent": "✗"}

    for day in range(1, num_days + 1):
        d     = f"{sel_year}-{sel_month:02d}-{day:02d}"
        d_obj = date(sel_year, sel_month, day)
        wday  = d_obj.weekday()
        rec   = rec_map.get(d)
        is_today = (d_obj == today)
        extra = " att-today" if is_today else ""

        if wday >= 5:
            cells.append(f'<span class="att-day att-weekend{extra}">{day}</span>')
        elif rec and rec.get("clock_in"):
            st_cls  = STATUS_STYLE.get(rec.get("status", "present"), "att-present")
            em      = STATUS_EMOJI.get(rec.get("status", "present"), "")
            ci_disp = rec.get("clock_in", "-")
            co_disp = rec.get("clock_out", "-")
            cells.append(f'<span class="att-day {st_cls}{extra}" title="{ci_disp}~{co_disp}">{day}{em}</span>')
        elif d_obj > today:
            cells.append(f'<span class="att-day att-future{extra}">{day}</span>')
        else:
            cells.append(f'<span class="att-day att-absent{extra}" title="결근">{day}✗</span>')

    # 7열로 렌더링
    while len(cells) % 7 != 0:
        cells.append("")

    for week_start in range(0, len(cells), 7):
        week = cells[week_start:week_start + 7]
        cols = st.columns(7)
        for i, cell in enumerate(week):
            cols[i].markdown(cell, unsafe_allow_html=True)

    # 범례
    st.markdown("""
    <div style='margin-top:.8rem;font-size:.78rem;color:#666;'>
    <span style='background:#c8e6c9;padding:2px 8px;border-radius:10px;margin-right:6px'>정상출근</span>
    <span style='background:#fff9c4;padding:2px 8px;border-radius:10px;margin-right:6px'>⚠ 지각</span>
    <span style='background:#ffcdd2;padding:2px 8px;border-radius:10px;margin-right:6px'>✗ 결근</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 상세 리스트
    st.markdown("#### 상세 내역")
    rows = []
    for day in range(1, num_days + 1):
        d     = f"{sel_year}-{sel_month:02d}-{day:02d}"
        d_obj = date(sel_year, sel_month, day)
        if d_obj.weekday() >= 5:
            continue
        rec = rec_map.get(d)
        if rec and rec.get("clock_in"):
            wm = rec.get("work_minutes", 0)
            st_lbl = {"present": "✅ 정상", "late": "⚠️ 지각",
                      "early_leave": "⏰ 조퇴", "absent": "❌ 결근"}.get(rec.get("status", "present"), "-")
            rows.append({
                "날짜": d, "요일": _WEEKDAY_KR[d_obj.weekday()],
                "출근": rec.get("clock_in", "-") or "-",
                "퇴근": rec.get("clock_out", "-") or "-",
                "근무시간": _fmt_min(wm) if wm else "-",
                "상태": st_lbl,
            })
        elif d_obj <= today:
            rows.append({
                "날짜": d, "요일": _WEEKDAY_KR[d_obj.weekday()],
                "출근": "-", "퇴근": "-", "근무시간": "-",
                "상태": "❌ 결근" if d_obj < today else "—",
            })

    if rows:
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=350)

        worked = sum(1 for r in rows if r["출근"] != "-")
        lates  = sum(1 for r in rows if "지각" in r["상태"])
        total_m = sum(r.get("work_minutes", 0) for r in rec_map.values())
        st.caption(f"근무: **{worked}일** | 지각: **{lates}회** | 총 근로: **{_fmt_min(total_m)}**")
    else:
        st.info("근태 기록이 없습니다.")


# ── 내 정보 탭 ────────────────────────────────────────────────
def _render_profile(user: dict):
    st.subheader("👤 내 정보")

    phone_display = ""
    if user.get("phone"):
        p = user["phone"].replace("-", "").replace(" ", "")
        phone_display = f"****-****-{p[-4:]}" if len(p) >= 4 else user["phone"]

    col1, col2 = st.columns(2)
    col1.markdown(f"**이름** : {user['name']}")
    col2.markdown(f"**소속지점** : {user['branch']}")
    col1.markdown(f"**이메일** : {user.get('email') or '—'}")
    col2.markdown(f"**전화번호** : {phone_display or '—'}")
    col1.markdown(f"**근무시간** : {user.get('work_start','09:00')} ~ {user.get('work_end','18:00')}")

    st.divider()
    st.subheader("🔑 비밀번호 변경")

    with st.form("profile_change_pw"):
        cur_pw  = st.text_input("현재 비밀번호", type="password")
        new_pw  = st.text_input("새 비밀번호 (6자 이상)", type="password")
        new_pw2 = st.text_input("새 비밀번호 확인", type="password")

        if st.form_submit_button("변경하기", type="primary"):
            from domains.payroll.db import verify_employee_login, update_employee_password
            if not verify_employee_login(user["username"], cur_pw):
                st.error("현재 비밀번호가 올바르지 않습니다.")
            elif len(new_pw) < 6:
                st.error("비밀번호는 6자 이상이어야 합니다.")
            elif new_pw != new_pw2:
                st.error("새 비밀번호가 일치하지 않습니다.")
            else:
                if update_employee_password(user["employee_id"], new_pw):
                    st.success("✅ 비밀번호가 변경되었습니다.")
                else:
                    st.error("변경 실패.")

    st.divider()
    if st.button("🚪 로그아웃", use_container_width=False):
        _logout()


# ── 라우팅 ───────────────────────────────────────────────────
user = _current_user()

if not user:
    _render_login()
elif user.get("must_change_pw"):
    _render_change_pw(user)
else:
    _render_main(user)
