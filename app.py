"""
app.py — WebSettle 진입점 (DDD 라우터)
모든 비즈니스 로직은 domains/ 와 shared/ 에 위치합니다.
"""
import streamlit as st
from datetime import datetime
from pathlib import Path

# ── 초기화 ────────────────────────────────────────────────────
from shared.db import init_db, load_keyword_rules
from domains.auth.service import init_users_table, get_session_user, delete_session
from domains.auth.ui import show_login
from domains.payroll.db import init_payroll_tables
from domains.branch.db import init_branch_tables
from shared.utils import get_logo_html

# ── 앱 기본 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="WebSettle · 라온스포츠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── DB 초기화 ─────────────────────────────────────────────────
init_db()
load_keyword_rules()
init_users_table()
init_payroll_tables()
init_branch_tables()

# ── 글로벌 CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');

/* ═══ LIGHT MODE ══════════════════════════════════════════════ */
:root {
  --red:#E60028; --reds:#FFE9EC; --redd:#C00022;
  --bg:#FAF7F5; --sf:#FFFFFF; --sf2:#F3EFEB; --sf3:#ECE7E2;
  --ink:#1F1B1B; --ink2:#5B5450; --ink3:#9A918C; --ink4:#C3BAB4;
  --bd:rgba(31,27,27,.09); --bds:rgba(31,27,27,.16);
  --pos:#2E7D5B; --poss:#E4F1EA;
  --warn:#B86E1F; --warns:#FBEEDB;
  --info:#3963A8; --infos:#E4ECF8;
  --sh:0 1px 3px rgba(31,27,27,.06),0 1px 2px rgba(31,27,27,.04);
  --shm:0 4px 20px rgba(31,27,27,.10);
  --r:14px; --rs:10px;
  --chart-ink:#1F1B1B;
}

/* ═══ DARK MODE ═══════════════════════════════════════════════ */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg:#161210; --sf:#1E1A18; --sf2:#272220; --sf3:#302B28;
    --ink:#EDE8E5; --ink2:#AEA69F; --ink3:#6A6158; --ink4:#3E3835;
    --bd:rgba(237,232,229,.08); --bds:rgba(237,232,229,.15);
    --reds:rgba(230,0,40,.20); --poss:rgba(46,125,91,.20);
    --warns:rgba(184,110,31,.20); --infos:rgba(57,99,168,.20);
    --sh:0 1px 4px rgba(0,0,0,.35),0 1px 2px rgba(0,0,0,.25);
    --shm:0 6px 24px rgba(0,0,0,.50);
    --chart-ink:#EDE8E5;
  }
}
[data-theme="dark"] {
  --bg:#161210; --sf:#1E1A18; --sf2:#272220; --sf3:#302B28;
  --ink:#EDE8E5; --ink2:#AEA69F; --ink3:#6A6158; --ink4:#3E3835;
  --bd:rgba(237,232,229,.08); --bds:rgba(237,232,229,.15);
  --reds:rgba(230,0,40,.20); --poss:rgba(46,125,91,.20);
  --warns:rgba(184,110,31,.20); --infos:rgba(57,99,168,.20);
  --sh:0 1px 4px rgba(0,0,0,.35),0 1px 2px rgba(0,0,0,.25);
  --shm:0 6px 24px rgba(0,0,0,.50);
  --chart-ink:#EDE8E5;
}

*{box-sizing:border-box}
html,body,[class*="css"]{
  font-family:'Pretendard Variable',Pretendard,-apple-system,system-ui,'Apple SD Gothic Neo',sans-serif!important;
  -webkit-font-smoothing:antialiased;
}
[data-testid="stAppViewContainer"]{background:var(--bg)!important}
header[data-testid="stHeader"]{display:none!important}
footer{display:none!important}
#MainMenu{display:none!important}

/* ── 커스텀 사이드바 제거 (Streamlit 기본) ─────────────── */
section[data-testid="stSidebar"]{display:none!important}
[data-testid="stSidebarCollapseButton"]{display:none!important}
button[data-testid="collapsedControl"]{display:none!important}

/* ── 커스텀 고정 사이드바 ───────────────────────────────── */
.c-sb{
  position:fixed;top:0;left:0;width:220px;height:100vh;
  background:var(--sf);border-right:1px solid var(--bd);
  z-index:9998;display:flex;flex-direction:column;
  box-shadow:1px 0 8px rgba(31,27,27,.04);
}
.c-sb-logo{padding:24px 18px 18px;border-bottom:1px solid var(--bd)}
.c-sb-nav{padding:8px 12px 20px;flex:1;overflow-y:auto}
.sb-sec{font-size:10px;color:var(--ink4);font-weight:700;letter-spacing:.08em;
  text-transform:uppercase;padding:12px 4px 6px}
.sb-item{display:flex;align-items:center;gap:10px;padding:9px 12px;
  border-radius:var(--rs);color:var(--ink2);font-size:13.5px;font-weight:500;
  text-decoration:none;letter-spacing:-.01em;transition:background .15s,color .15s;
  margin-bottom:2px;border-left:3px solid transparent}
.sb-item:hover{background:var(--sf2);color:var(--ink)}
.sb-item.on{background:var(--sf2);color:var(--ink);font-weight:700;border-left-color:var(--red)}
.sb-item svg{width:17px;height:17px;flex-shrink:0;stroke:currentColor;fill:none;
  stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;opacity:.6}
.sb-item.on svg{opacity:1}
.sb-foot{padding:12px 16px;border-top:1px solid var(--bd)}
.theme-btn{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--ink3);
  text-decoration:none;padding:6px 8px;border-radius:var(--rs);transition:background .15s}
.theme-btn:hover{background:var(--sf2);color:var(--ink)}

@media(min-width:768px){
  [data-testid="stMain"]{margin-left:220px!important;width:calc(100% - 220px)!important}
  [data-testid="stMainBlockContainer"]{padding:0 2rem 3rem!important;max-width:100%!important;box-sizing:border-box!important}
  section.main,.main{margin-left:220px!important}
  .main .block-container{padding:0 2rem 3rem!important;max-width:100%!important}
  [data-testid="stAppViewContainer"]{padding-left:220px!important;box-sizing:border-box!important}
}

/* ── Mobile header ───────────────────────────────────────── */
.mob-hd{display:none;justify-content:center;align-items:center;padding:14px 0 10px;margin-bottom:4px}
.mob-hd img,.mob-hd svg{max-width:180px;height:auto}

/* ── Filter bar ──────────────────────────────────────────── */
.filter-wrap{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  padding:14px 18px;margin-bottom:20px;box-shadow:var(--sh)}

/* ── Bottom nav (mobile) ─────────────────────────────────── */
.bnav{display:none;position:fixed;bottom:0;left:0;right:0;height:62px;
  background:var(--sf);border-top:1px solid var(--bd);
  justify-content:space-around;align-items:stretch;z-index:9999;
  padding-bottom:env(safe-area-inset-bottom,0px)}
.bnav a{display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:3px;flex:1;text-decoration:none;color:var(--ink3);font-size:10px;font-weight:600;
  padding:6px 0;transition:color .15s}
.bnav a.on{color:var(--red)}
.bnav svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.8;
  stroke-linecap:round;stroke-linejoin:round}

/* ── Page header ──────────────────────────────────────────── */
.ph{padding:20px 0 16px;border-bottom:1px solid var(--bd);margin-bottom:22px}
.ph-title{font-size:21px;font-weight:700;letter-spacing:-.025em;color:var(--ink)}
.ph-sub{font-size:12px;color:var(--ink3);margin-top:3px}

/* ── KPI grid ─────────────────────────────────────────────── */
.kpi-grid{display:grid;gap:14px;margin-bottom:24px;grid-template-columns:repeat(5,1fr)}
.kpi{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  padding:18px 20px;box-shadow:var(--sh);position:relative;overflow:hidden;
  transition:box-shadow .2s,transform .15s}
.kpi:hover{box-shadow:var(--shm);transform:translateY(-1px)}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,var(--red),rgba(230,0,40,.3));border-radius:var(--r) var(--r) 0 0}
.kpi-lbl{font-size:10.5px;color:var(--ink3);font-weight:600;letter-spacing:.05em;text-transform:uppercase}
.kpi-val{font-size:clamp(17px,2.1vw,30px);font-weight:800;letter-spacing:-.03em;margin-top:10px;
  font-feature-settings:'tnum' 1;line-height:1.05;display:flex;align-items:baseline;gap:4px}
.kpi-unit{font-size:clamp(11px,1vw,15px);font-weight:500;color:var(--ink3)}
.kpi-sub{font-size:clamp(9px,0.8vw,11px);color:var(--ink3);margin-top:6px}
.c-ink{color:var(--ink)} .c-red{color:var(--red)} .c-pos{color:var(--pos)}
.c-warn{color:var(--warn)} .c-info{color:var(--info)}

/* ── Section label ────────────────────────────────────────── */
.sec{display:flex;align-items:center;gap:10px;margin:28px 0 16px}
.sec-t{font-size:10.5px;font-weight:700;color:var(--ink4);letter-spacing:.09em;text-transform:uppercase;white-space:nowrap}
.sec-l{flex:1;height:1px;background:linear-gradient(90deg,var(--bds),transparent)}

/* ── Branch table ─────────────────────────────────────────── */
.bt{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  overflow:hidden;box-shadow:var(--sh);width:100%}
.bt table{width:100%;border-collapse:collapse;table-layout:fixed}
.bt th{padding:11px 16px;background:var(--sf2);border-bottom:1px solid var(--bds);
  border-right:1px solid var(--bd);font-size:10px;color:var(--ink4);font-weight:700;
  text-transform:uppercase;letter-spacing:.06em;text-align:right;white-space:nowrap}
.bt th:first-child{text-align:left;width:22%}
.bt th:last-child{border-right:none;width:24%}
.bt th:not(:first-child):not(:last-child){width:18%}
.bt td{padding:13px 16px;border-bottom:1px solid var(--bd);border-right:1px solid var(--bd);
  font-size:13.5px;text-align:right;color:var(--ink2);font-feature-settings:'tnum' 1;vertical-align:middle}
.bt td:first-child{text-align:left;border-right:1px solid var(--bds);font-weight:600;color:var(--ink)}
.bt td:last-child{border-right:none}
.bt tr:last-child td{border-bottom:none}
.bt tr:hover td{background:var(--sf2);transition:background .12s}
.bt tr.sel td{background:var(--reds)!important}
.n{font-feature-settings:'tnum' 1;text-align:right;color:var(--ink2)}
.bdg{display:inline-flex;align-items:center;gap:3px;padding:3px 9px;
  border-radius:999px;font-size:11.5px;font-weight:600}
.bdg-pos{background:var(--poss);color:var(--pos)}
.bdg-neg{background:var(--reds);color:var(--red)}
.bdg-neu{background:var(--sf2);color:var(--ink2)}

/* ── Detail panel ─────────────────────────────────────────── */
.dp{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  padding:24px;box-shadow:var(--shm);margin-top:4px;margin-bottom:20px}
.dp-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;flex-wrap:wrap;gap:8px}
.dp-title{font-size:17px;font-weight:700;color:var(--ink);letter-spacing:-.02em}
.dp-profit{display:flex;align-items:center;gap:10px}
.dp-profit-val{font-size:18px;font-weight:700;font-feature-settings:'tnum' 1}
.dp-profit-rate{font-size:13px;font-weight:600;padding:3px 10px;border-radius:999px}
.dp-cols{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.dp-sec{margin-bottom:0}
.dp-sec-t{font-size:10.5px;font-weight:700;color:var(--ink3);letter-spacing:.07em;
  text-transform:uppercase;padding-bottom:8px;border-bottom:1px solid var(--bd);margin-bottom:0}
.dp-row{display:flex;justify-content:space-between;align-items:center;
  padding:8px 0;border-bottom:1px solid var(--bd);font-size:13px}
.dp-row:last-child{border-bottom:none}
.dp-row.sub{padding:6px 0 6px 14px;font-size:12px;color:var(--ink3)}
.dp-row.tot{padding:11px 0;font-weight:700;font-size:14px;border-top:1px solid var(--bds)}
.dp-lbl{color:var(--ink2)} .dp-lbl.m{color:var(--ink);font-weight:600}
.dp-amt{font-feature-settings:'tnum' 1;font-weight:600;text-align:right}

/* ── Chart card ───────────────────────────────────────────── */
.ch{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  padding:20px 20px 8px;box-shadow:var(--sh);margin-bottom:20px}
.ch-t{font-size:14px;font-weight:700;color:var(--ink);margin-bottom:3px;letter-spacing:-.02em}
.ch-s{font-size:11px;color:var(--ink3);margin-bottom:10px}

/* ── PDF section ──────────────────────────────────────────── */
.pdf-box{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  padding:20px 22px;box-shadow:var(--sh);margin-top:24px}
.pdf-t{font-size:14px;font-weight:600;color:var(--ink);margin-bottom:14px}

/* ── Alert ────────────────────────────────────────────────── */
.al{padding:12px 16px;border-radius:var(--rs);font-size:13px;margin-bottom:16px;border:1px solid}
.al-info{background:var(--infos);border-color:rgba(57,99,168,.2);color:var(--info)}
.al-warn{background:var(--warns);border-color:rgba(184,110,31,.2);color:var(--warn)}
.al-ok  {background:var(--poss);border-color:rgba(46,125,91,.2);color:var(--pos)}

/* ── Mobile ───────────────────────────────────────────────── */
@media(max-width:767px){
  .kpi-grid{grid-template-columns:repeat(2,1fr)}
  .dp-cols{grid-template-columns:1fr}
  .c-sb{display:none}
  .bnav{display:flex}
  .mob-hd{display:flex}
}
</style>
""", unsafe_allow_html=True)

# ── 테마 처리 ─────────────────────────────────────────────────
_theme_param = st.query_params.get("theme", None)
if _theme_param in ("dark", "light"):
    st.session_state["theme"] = _theme_param
_theme = st.session_state.get("theme", "auto")

if _theme == "dark":
    st.markdown("""<style>
    :root{
      --bg:#161210!important;--sf:#1E1A18!important;--sf2:#272220!important;--sf3:#302B28!important;
      --ink:#EDE8E5!important;--ink2:#AEA69F!important;--ink3:#6A6158!important;--ink4:#3E3835!important;
      --bd:rgba(237,232,229,.08)!important;--bds:rgba(237,232,229,.15)!important;
      --reds:rgba(230,0,40,.20)!important;--poss:rgba(46,125,91,.20)!important;
      --warns:rgba(184,110,31,.20)!important;--infos:rgba(57,99,168,.20)!important;
      --sh:0 1px 4px rgba(0,0,0,.35),0 1px 2px rgba(0,0,0,.25)!important;
      --shm:0 6px 24px rgba(0,0,0,.50)!important;
    }
    </style>""", unsafe_allow_html=True)
elif _theme == "light":
    st.markdown("""<style>
    @media(prefers-color-scheme:dark){
      :root{
        --bg:#FAF7F5!important;--sf:#FFFFFF!important;--sf2:#F3EFEB!important;--sf3:#ECE7E2!important;
        --ink:#1F1B1B!important;--ink2:#5B5450!important;--ink3:#9A918C!important;--ink4:#C3BAB4!important;
        --bd:rgba(31,27,27,.09)!important;--bds:rgba(31,27,27,.16)!important;
      }
    }
    </style>""", unsafe_allow_html=True)

# ── 인증 ──────────────────────────────────────────────────────
_session_token = st.query_params.get("t", "")
if not st.session_state.get("authenticated", False):
    if _session_token:
        _user = get_session_user(_session_token)
        if _user:
            st.session_state.authenticated  = True
            st.session_state.auth_user      = _user
            st.session_state.session_token  = _session_token

if not st.session_state.get("authenticated", False):
    show_login()
    st.stop()

_auth_user     = st.session_state.auth_user
_session_token = st.session_state.get("session_token", _session_token)

# ── 라우팅 ────────────────────────────────────────────────────
page = st.query_params.get("page", "dashboard")
_now = datetime.now()
for k, v in [("year", _now.year), ("month", _now.month), ("sel_br", "전체"), ("drill", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── SVG 아이콘 ────────────────────────────────────────────────
I_DASH   = '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/></svg>'
I_BRANCH = '<svg viewBox="0 0 24 24"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
I_UP     = '<svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>'
I_PAY    = '<svg viewBox="0 0 24 24"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>'
I_RULE   = '<svg viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="12" y2="16"/></svg>'
I_MOON   = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
I_SUN    = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'

# ── 사이드바 렌더링 ───────────────────────────────────────────
def _render_sidebar():
    logo_h = get_logo_html(mobile=False)
    items  = [
        ("dashboard", "대시보드",      I_DASH),
        ("branch",    "지점 상세",     I_BRANCH),
        ("payroll",   "급여 계산",     I_PAY),
        ("upload",    "데이터 업로드", I_UP),
        ("rules",     "규칙 관리",     I_RULE),
    ]
    if _auth_user.get("role") == "admin":
        items.append(("accounts", "계정 관리", "👤 "))

    nav = "".join(
        f'<a href="?page={p}&t={_session_token}" target="_self" class="sb-item {"on" if page == p else ""}">'
        f'{ic}{lbl}</a>'
        for p, lbl, ic in items
    )

    role_lbl  = "관리자" if _auth_user.get("role") == "admin" else "사용자"
    user_html = (
        f'<div style="padding:12px 16px;margin:8px 0;background:var(--sf2);border-radius:var(--rs)">'
        f'<div style="font-size:12px;color:var(--ink3);margin-bottom:2px">{role_lbl}</div>'
        f'<div style="font-size:14px;font-weight:600;color:var(--ink)">{_auth_user.get("name","")}</div>'
        f'</div>'
    )

    if _theme == "light":
        _next_theme, _theme_icon, _theme_lbl = "dark",  I_MOON, "다크 모드"
    else:
        _next_theme, _theme_icon, _theme_lbl = "light", I_SUN,  "라이트 모드"
    theme_link = (
        f'<a href="?page={page}&t={_session_token}&theme={_next_theme}" '
        f'target="_self" class="theme-btn">{_theme_icon} {_theme_lbl}</a>'
    )

    st.markdown(f"""
    <div class="c-sb">
      <div class="c-sb-logo">{logo_h}</div>
      <div class="c-sb-nav">
        <div class="sb-sec">WORKSPACE</div>
        {nav}
        <div style="margin-top:16px">{user_html}</div>
      </div>
      <div class="sb-foot">{theme_link}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    if st.button("🚪 로그아웃", use_container_width=True, key="logout_btn"):
        delete_session(_session_token)
        st.session_state.authenticated = False
        st.session_state.auth_user     = {}
        st.session_state.session_token = ""
        st.query_params.clear()
        st.rerun()


def _render_bnav():
    items = [
        ("dashboard", "대시보드", I_DASH),
        ("branch",    "지점",     I_BRANCH),
        ("payroll",   "급여",     I_PAY),
        ("upload",    "업로드",   I_UP),
        ("rules",     "규칙",     I_RULE),
    ]
    h = '<div class="bnav">'
    for p, lbl, ic in items:
        cls = "on" if page == p else ""
        h  += f'<a href="?page={p}&t={_session_token}" target="_self" class="{cls}">{ic}<span>{lbl}</span></a>'
    h += '</div>'
    st.markdown(h, unsafe_allow_html=True)


# ── 공통 네비게이션 렌더 ─────────────────────────────────────
_render_sidebar()
_render_bnav()
st.markdown(f'<div class="mob-hd">{get_logo_html(mobile=True)}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  페이지 라우팅
# ══════════════════════════════════════════════════════════════
if page == "dashboard":
    from domains.dashboard.ui import render_page
    render_page()

elif page == "branch":
    from domains.branch.ui import render_page
    render_page()

elif page == "payroll":
    from domains.payroll.ui import render_page
    render_page()

elif page == "upload":
    from domains.upload.ui import render_page
    render_page()

elif page == "rules":
    from domains.rules.ui import render_page
    render_page()

elif page == "accounts":
    from domains.accounts.ui import render_page
    render_page(_auth_user)

else:
    from domains.dashboard.ui import render_page
    render_page()
