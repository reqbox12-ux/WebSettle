import streamlit as st
import pandas as pd
import json, base64
import tempfile, os
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go

from modules.db import (
    init_db, load_keyword_rules,
    upsert_card_sales, upsert_bank_transactions, upsert_payroll,
    get_card_by_branch, get_branch_cash_revenue,
    get_expense_by_category, get_payroll_summary,
    get_unreviewed_transactions, get_all_bank_transactions,
    update_transaction_classification,
    get_keyword_rules, EXPENSE_CATEGORIES,
)
from modules.parser import (
    parse_card_aggregate, parse_credit_card,
    parse_hana, parse_shinhan,
    parse_bank_auto, recalc_vat,
    parse_payroll_freelance, parse_payroll_insured,
)
from modules.classifier import classify_transactions, add_rule
from modules.auth import (
    init_users_table, verify_login, get_user_by_username,
    get_all_users, add_user, delete_user, change_password,
    make_token, validate_token, TOKEN_COOKIE,
)
import extra_streamlit_components as stx
from modules.ai_classifier import (
    load_api_key, save_api_key,
    ai_classify_batch, ai_extract_keyword,
)

MAPPING_PATH = Path("mapping/branch_mapping.json")
with open(MAPPING_PATH, encoding="utf-8") as f:
    _mapping = json.load(f)
BRANCH_LIST = _mapping["branch_list"]

ALL_CATEGORIES = [
    "기타매출(현금)", "기타매출(카드)", "PT매출(현금)", "PT매출(카드)",
    "GX매출(현금)", "GX매출(카드)", "골프매출(현금)", "골프매출(카드)",
    "키즈매출(현금)", "키즈매출(카드)", "도급비", "시설상환비", "카페매출",
] + EXPENSE_CATEGORIES + ["제외"]

st.set_page_config(
    page_title="WebSettle · 라온스포츠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');

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

/* ── Streamlit 기본 사이드바 완전 제거 ─────── */
section[data-testid="stSidebar"]{display:none!important}
[data-testid="stSidebarCollapseButton"]{display:none!important}
button[data-testid="collapsedControl"]{display:none!important}

/* ── 커스텀 고정 사이드바 (PC) ──────────────── */
.c-sb{
  position:fixed;top:0;left:0;width:220px;height:100vh;
  background:var(--sf);border-right:1px solid var(--bd);
  z-index:9998;display:flex;flex-direction:column;
  box-shadow:1px 0 8px rgba(31,27,27,.04);
}
.c-sb-logo{padding:24px 18px 18px;border-bottom:1px solid var(--bd)}
.c-sb-nav{padding:8px 12px 20px;flex:1}
.sb-sec{font-size:10px;color:var(--ink4);font-weight:700;letter-spacing:.08em;
  text-transform:uppercase;padding:12px 4px 6px}
.sb-item{display:flex;align-items:center;gap:10px;padding:9px 12px;
  border-radius:var(--rs);color:var(--ink2);font-size:13.5px;font-weight:500;
  text-decoration:none;letter-spacing:-.01em;transition:background .15s,color .15s;
  margin-bottom:2px;border-left:3px solid transparent}
.sb-item:hover{background:var(--sf2);color:var(--ink)}
.sb-item.on{background:var(--sf2);color:var(--ink);font-weight:700;
  border-left-color:var(--red)}
.sb-item svg{width:17px;height:17px;flex-shrink:0;stroke:currentColor;fill:none;
  stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;opacity:.6}
.sb-item.on svg{opacity:1}

/* 메인 컨텐츠를 사이드바 오른쪽으로 밀기 (Streamlit 1.57) */
@media(min-width:768px){
  /* Streamlit 1.44+ 셀렉터 */
  [data-testid="stMain"]{margin-left:220px!important;width:calc(100% - 220px)!important}
  [data-testid="stMainBlockContainer"]{padding:0 2rem 3rem!important;max-width:100%!important;box-sizing:border-box!important}
  /* 구버전 호환 */
  section.main,.main{margin-left:220px!important}
  .main .block-container{padding:0 2rem 3rem!important;max-width:100%!important}
  /* AppViewContainer 레벨 */
  [data-testid="stAppViewContainer"]{padding-left:220px!important;box-sizing:border-box!important}
}
/* ── Mobile header (logo top-center) ────────── */
.mob-hd{display:none;justify-content:center;align-items:center;
  padding:14px 0 10px;margin-bottom:4px}
.mob-hd img,.mob-hd svg{max-width:180px;height:auto}

/* ── Filter bar ─────────────────────────────── */
.filter-wrap{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  padding:14px 18px;margin-bottom:20px;box-shadow:var(--sh)}

/* ── Bottom nav (mobile) ────────────────────── */
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

/* ── Page header ────────────────────────────── */
.ph{padding:20px 0 16px;border-bottom:1px solid var(--bd);margin-bottom:22px}
.ph-title{font-size:21px;font-weight:700;letter-spacing:-.025em;color:var(--ink)}
.ph-sub{font-size:12px;color:var(--ink3);margin-top:3px}

/* ── KPI grid ───────────────────────────────── */
.kpi-grid{display:grid;gap:14px;margin-bottom:24px;grid-template-columns:repeat(5,1fr)}
.kpi{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  padding:18px 20px;box-shadow:var(--sh)}
.kpi-lbl{font-size:10.5px;color:var(--ink3);font-weight:600;letter-spacing:.05em;text-transform:uppercase}
.kpi-val{font-size:clamp(17px,2.1vw,30px);font-weight:800;letter-spacing:-.03em;margin-top:10px;
  font-feature-settings:'tnum' 1;line-height:1.05;display:flex;align-items:baseline;gap:4px}
.kpi-unit{font-size:clamp(11px,1vw,15px);font-weight:500;color:var(--ink3)}
.kpi-sub{font-size:clamp(9px,0.8vw,11px);color:var(--ink3);margin-top:6px}
.c-ink{color:var(--ink)} .c-red{color:var(--red)} .c-pos{color:var(--pos)}
.c-warn{color:var(--warn)} .c-info{color:var(--info)}

/* ── Section label ──────────────────────────── */
.sec{display:flex;align-items:center;gap:10px;margin:24px 0 14px}
.sec-t{font-size:11px;font-weight:700;color:var(--ink3);letter-spacing:.07em;text-transform:uppercase;white-space:nowrap}
.sec-l{flex:1;height:1px;background:var(--bd)}

/* ── Branch table ───────────────────────────── */
.bt{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  overflow:hidden;box-shadow:var(--sh);width:100%}
.bt table{width:100%;border-collapse:collapse;table-layout:fixed}
.bt th{padding:10px 16px;background:var(--sf2);border-bottom:2px solid var(--bd);
  border-right:1px solid var(--bd);font-size:10.5px;color:var(--ink3);font-weight:700;
  text-transform:uppercase;letter-spacing:.04em;text-align:right;white-space:nowrap}
.bt th:first-child{text-align:left;width:22%}
.bt th:last-child{border-right:none;width:24%}
.bt th:not(:first-child):not(:last-child){width:18%}
.bt td{padding:13px 16px;border-bottom:1px solid var(--bd);border-right:1px solid var(--bd);
  font-size:13.5px;text-align:right;color:var(--ink2);
  font-feature-settings:'tnum' 1;vertical-align:middle}
.bt td:first-child{text-align:left;border-right:1px solid var(--bds);font-weight:600;color:var(--ink)}
.bt td:last-child{border-right:none}
.bt tr:last-child td{border-bottom:none}
.bt tr:hover td{background:var(--sf2)}
.bt tr.sel td{background:var(--reds)!important}
.n{font-feature-settings:'tnum' 1;text-align:right;color:var(--ink2)}
.bdg{display:inline-flex;align-items:center;gap:3px;padding:3px 9px;
  border-radius:999px;font-size:11.5px;font-weight:600}
.bdg-pos{background:var(--poss);color:var(--pos)}
.bdg-neg{background:var(--reds);color:var(--red)}
.bdg-neu{background:var(--sf2);color:var(--ink2)}

/* ── Detail panel ───────────────────────────── */
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

/* ── Chart card ─────────────────────────────── */
.ch{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  padding:20px 20px 6px;box-shadow:var(--sh);margin-bottom:20px}
.ch-t{font-size:14px;font-weight:600;color:var(--ink);margin-bottom:2px}
.ch-s{font-size:11.5px;color:var(--ink3);margin-bottom:8px}

/* ── PDF section ────────────────────────────── */
.pdf-box{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);
  padding:20px 22px;box-shadow:var(--sh);margin-top:24px}
.pdf-t{font-size:14px;font-weight:600;color:var(--ink);margin-bottom:14px}

/* ── Alert ──────────────────────────────────── */
.al{padding:12px 16px;border-radius:var(--rs);font-size:13px;font-weight:500;
  margin-bottom:14px;display:flex;gap:10px;line-height:1.5}
.al-info{background:var(--infos);border-left:3px solid var(--info);color:var(--ink)}
.al-warn{background:var(--warns);border-left:3px solid var(--warn);color:var(--ink)}
.al-ok{background:var(--poss);border-left:3px solid var(--pos);color:var(--ink)}

/* ── Widgets ────────────────────────────────── */
.stButton>button{background:var(--ink)!important;color:#FAF7F5!important;
  border:none!important;border-radius:var(--rs)!important;
  font-weight:600!important;font-size:13.5px!important;padding:7px 16px!important;letter-spacing:-.01em!important}
.stButton>button:hover{background:#2A2625!important}
.stButton>button[kind="primary"]{background:var(--red)!important}
.stButton>button[kind="primary"]:hover{background:var(--redd)!important}
.stButton>button[kind="secondary"]{background:var(--sf2)!important;color:var(--ink)!important}
[data-baseweb="select"]>div:first-child{border-radius:var(--rs)!important;
  border-color:var(--bds)!important;font-size:13.5px!important}
[data-baseweb="input"]>div{border-radius:var(--rs)!important}
[data-testid="stTabs"] [data-baseweb="tab-list"]{background:transparent!important;
  border-bottom:1px solid var(--bd);gap:0}
[data-testid="stTabs"] [data-baseweb="tab"]{background:transparent!important;
  border-radius:0!important;border-bottom:2px solid transparent!important;
  padding:10px 18px!important;font-size:13.5px!important;font-weight:500!important;color:var(--ink3)!important}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--ink)!important;
  font-weight:700!important;border-bottom-color:var(--red)!important}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{display:none!important}
[data-testid="stDataFrame"]{border-radius:var(--r)!important;border:1px solid var(--bd)!important;
  overflow:hidden!important;box-shadow:var(--sh)!important}
[data-testid="stExpander"]{border:1px solid var(--bd)!important;
  border-radius:var(--r)!important;background:var(--sf)!important;margin-bottom:8px!important}
[data-testid="stCheckbox"] label{font-size:13.5px!important;font-weight:500!important}
/* ── Radio button label visibility ─────────── */
[data-testid="stRadio"] label p,
[data-testid="stRadio"] label span,
[data-testid="stRadio"] p,
[data-testid="stRadio"] span{color:var(--ink)!important}
[data-testid="stRadio"] label{color:var(--ink)!important}

/* ── Mobile ─────────────────────────────────── */
@media(max-width:767px){
  .c-sb{display:none!important}
  .bnav{display:flex!important}
  .mob-hd{display:flex!important}
  [data-testid="stMain"],section.main,.main{margin-left:0!important;width:100%!important}
  [data-testid="stAppViewContainer"]{padding-left:0!important}
  [data-testid="stMainBlockContainer"],.main .block-container{padding:.75rem .75rem 80px!important;max-width:100%!important}
  .kpi-grid{grid-template-columns:repeat(2,1fr);gap:10px}
  .bt table{table-layout:auto}
  .bt th:nth-child(2),.bt th:nth-child(3),.bt th:nth-child(4),
  .bt td:nth-child(2),.bt td:nth-child(3),.bt td:nth-child(4){display:none}
  .bt th,.bt td{padding:10px 10px}
  .dp-cols{grid-template-columns:1fr}
  .ph{padding:14px 0 12px}
  .ph-title{font-size:18px}
}
</style>
""", unsafe_allow_html=True)

init_db()
load_keyword_rules()
init_users_table()

# ── 쿠키 매니저 (로그인 유지용) ──────────────────────────────
@st.cache_resource
def _get_cookie_mgr():
    return stx.CookieManager(key="laon_ws")

_cookie_mgr = _get_cookie_mgr()

# ══════════════════════════════════════════════════════════════════════
#  로그인 페이지
# ══════════════════════════════════════════════════════════════════════
def _show_login():
    st.markdown("""<style>
    #MainMenu,header,footer{visibility:hidden}
    .login-title{font-size:24px;font-weight:700;color:#1F1B1B;margin-bottom:4px;text-align:center}
    .login-sub{font-size:13px;color:#9A918C;text-align:center;margin-bottom:24px}
    </style>""", unsafe_allow_html=True)

    st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)
    col = st.columns([1, 1, 1])[1]
    with col:
        st.markdown('<div style="text-align:center;font-size:36px;font-weight:900;color:#E60028;letter-spacing:-1px">LAON</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-title">WebSettle</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">라온스포츠 정산 시스템</div>', unsafe_allow_html=True)
        username = st.text_input("아이디", placeholder="아이디를 입력하세요", key="login_user")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key="login_pw")
        if st.button("로그인", type="primary", use_container_width=True, key="login_btn"):
            user = verify_login(username, password)
            if user:
                token = make_token(user["username"])
                _cookie_mgr.set(TOKEN_COOKIE, token, max_age=30 * 24 * 3600)  # 30일
                st.session_state.authenticated = True
                st.session_state.auth_user     = user
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

# ── 인증 체크 (session_state → 쿠키 순서로 확인) ─────────────
if not st.session_state.get("authenticated", False):
    # 쿠키에 토큰이 있으면 자동 로그인
    _token = _cookie_mgr.get(TOKEN_COOKIE)
    if _token:
        _uname = validate_token(_token)
        if _uname:
            _user = get_user_by_username(_uname)
            if _user:
                st.session_state.authenticated = True
                st.session_state.auth_user     = _user

if not st.session_state.get("authenticated", False):
    _show_login()
    st.stop()

_auth_user = st.session_state.auth_user   # {"username","name","role"}

# ══════════════════════════════════════════════════════════════════════
#  State & routing
# ══════════════════════════════════════════════════════════════════════
page = st.query_params.get('page', 'dashboard')
_now = datetime.now()
for k, v in [('year', _now.year), ('month', _now.month), ('sel_br', '전체'), ('drill', None)]:
    if k not in st.session_state:
        st.session_state[k] = v

_api_key = load_api_key()   # Anthropic API 키 (없으면 빈 문자열)

# ══════════════════════════════════════════════════════════════════════
#  SVG icons
# ══════════════════════════════════════════════════════════════════════
I_DASH   = '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/></svg>'
I_BRANCH = '<svg viewBox="0 0 24 24"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
I_UP     = '<svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>'
I_RULE   = '<svg viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="12" y2="16"/></svg>'
I_PDF    = '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/><line x1="10" y1="9" x2="10" y2="9"/></svg>'
I_CLOSE  = '<svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'

# LAON SPORTS wordmark SVG (fallback when logo.png not found)
I_LAON_SVG = '''<svg viewBox="0 0 210 80" xmlns="http://www.w3.org/2000/svg" style="width:140px;height:auto;display:block">
  <text x="2" y="56" fill="#E60028" font-size="62" font-weight="900"
    font-family="Arial Black,Impact,system-ui,sans-serif" letter-spacing="-3">LAON</text>
  <text x="7" y="74" fill="#E60028" font-size="13.5" font-weight="700"
    font-family="Arial,Helvetica,system-ui,sans-serif" letter-spacing="10">SPORTS</text>
</svg>'''

def get_logo_html(mobile=False):
    """Return logo HTML — uses assets/logo.png if available, else SVG fallback."""
    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        b64 = base64.b64encode(logo_path.read_bytes()).decode()
        w = "160" if mobile else "148"
        return f'<img src="data:image/png;base64,{b64}" style="width:{w}px;height:auto;display:block" alt="LAON SPORTS">'
    w = "160" if mobile else "140"
    return f'<svg viewBox="0 0 210 80" xmlns="http://www.w3.org/2000/svg" style="width:{w}px;height:auto;display:block"><text x="2" y="56" fill="#E60028" font-size="62" font-weight="900" font-family="Arial Black,Impact,system-ui,sans-serif" letter-spacing="-3">LAON</text><text x="7" y="74" fill="#E60028" font-size="13.5" font-weight="700" font-family="Arial,Helvetica,system-ui,sans-serif" letter-spacing="10">SPORTS</text></svg>'

# ══════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════
def fw(n, unit='auto'):
    try:
        v = int(n)
        if unit == 'auto':
            if abs(v) >= 100_000_000: return f"{v/100_000_000:.1f}억"
            if abs(v) >= 10_000:      return f"{v/10_000:.0f}만"
        return f"{v:,}"
    except: return "—"

def fn(n):
    try: return f"{int(n):,}"
    except: return "—"

def tone(v):
    if v > 0: return 'c-pos'
    if v < 0: return 'c-red'
    return 'c-ink'

def sec(label):
    st.markdown(f'<div class="sec"><span class="sec-t">{label}</span><span class="sec-l"></span></div>', unsafe_allow_html=True)

PLOT_BASE = dict(
    font=dict(family="Pretendard Variable,sans-serif", size=12, color="#1F1B1B"),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=16, b=36, l=10, r=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=12, color="#1F1B1B")),
    hoverlabel=dict(bgcolor="#fff", bordercolor="rgba(31,27,27,.12)",
                    font=dict(family="Pretendard Variable,sans-serif", size=13, color="#1F1B1B")),
)

# ══════════════════════════════════════════════════════════════════════
#  Data
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def c_card(y, m): return get_card_by_branch(y, m)
@st.cache_data(ttl=300, show_spinner=False)
def c_cash(y, m): return get_branch_cash_revenue(y, m)
@st.cache_data(ttl=300, show_spinner=False)
def c_pay(y, m):  return get_payroll_summary(y, m)
@st.cache_data(ttl=300, show_spinner=False)
def c_exp(y, m):  return get_expense_by_category(y, m)

def build_summary(year, month):
    card_df = c_card(year, month); cash_df = c_cash(year, month)
    pay_df  = c_pay(year, month);  exp_df  = c_exp(year, month)

    def s(df, col): return df.set_index("branch")[col] if not df.empty else pd.Series(dtype=float)

    card_sup = s(card_df, "card_supply"); card_fee = s(card_df, "card_fee")
    card_vat = s(card_df, "card_vat");   card_net = s(card_df, "card_net")
    cash_sup = s(cash_df, "cash_supply"); cash_vat = s(cash_df, "cash_vat")

    if not pay_df.empty:
        ins  = pay_df[pay_df.type=="insured"].groupby("branch")["net_pay"].sum()
        ins4 = pay_df[pay_df.type=="insured"].groupby("branch")["insurance"].sum()
        ins_t= pay_df[pay_df.type=="insured"].groupby("branch")["income_tax"].sum()
        frl  = pay_df[pay_df.type=="freelance"].groupby("branch")["net_pay"].sum()
        frl_t= pay_df[pay_df.type=="freelance"].groupby("branch")["income_tax"].sum()
        frl_l= pay_df[pay_df.type=="freelance"].groupby("branch")["local_tax"].sum()
    else:
        ins=ins4=ins_t=frl=frl_t=frl_l = pd.Series(dtype=float)

    pc = {"급여","4대보험료","소득세·지방세 합계","프리랜서","퇴직금"}
    other = (exp_df[~exp_df.category.isin(pc)].groupby("branch")["amount"].sum()
             if not exp_df.empty else pd.Series(dtype=float))

    r = pd.DataFrame({"branch": BRANCH_LIST}).set_index("branch")
    r["카드공급가액"] = card_sup; r["카드VAT"] = card_vat
    r["카드수수료"]   = card_fee; r["카드실수령"] = card_net
    r["현금VAT"]     = cash_vat; r["현금공급가액"] = cash_sup
    r["총매출"]      = r["카드실수령"].fillna(0) + r["현금공급가액"].fillna(0)
    r["부가세합계"]   = r["카드VAT"].fillna(0) + r["현금VAT"].fillna(0)
    r["급여"]=ins; r["4대보험료"]=ins4; r["소득세지방세"]=ins_t
    r["프리랜서"]=frl; r["프리랜서세금"]=frl_t+frl_l; r["기타지출"]=other
    r = r.fillna(0)
    r["인건비합계"] = r["급여"]+r["4대보험료"]+r["소득세지방세"]+r["프리랜서"]+r["프리랜서세금"]
    r["총지출"]     = r["부가세합계"]+r["인건비합계"]+r["기타지출"]
    r["손익"]       = r["총매출"]-r["총지출"]
    r["이익률"]     = r.apply(lambda x: round(x["손익"]/x["총매출"]*100,1) if x["총매출"]>0 else 0, axis=1)
    return r.reset_index()

# ══════════════════════════════════════════════════════════════════════
#  Sidebar (PC)
# ══════════════════════════════════════════════════════════════════════
def render_sidebar():
    logo_h = get_logo_html(mobile=False)
    items = [('dashboard','대시보드',I_DASH),('branch','지점 상세',I_BRANCH),('upload','데이터 업로드',I_UP),('rules','규칙 관리',I_RULE)]
    if _auth_user.get("role") == "admin":
        items.append(('accounts','계정 관리','👤 '))
    nav = ""
    for p, lbl, ic in items:
        cls = 'on' if page == p else ''
        nav += f'<a href="?page={p}" target="_self" class="sb-item {cls}">{ic}{lbl}</a>'

    role_lbl = "관리자" if _auth_user.get("role") == "admin" else "사용자"
    user_html = f'''<div style="padding:12px 16px;margin:8px 0;background:var(--sf2);border-radius:var(--rs)">
      <div style="font-size:12px;color:var(--ink3);margin-bottom:2px">{role_lbl}</div>
      <div style="font-size:14px;font-weight:600;color:var(--ink)">{_auth_user.get("name","")}</div>
    </div>'''

    html = f'''<div class="c-sb">
      <div class="c-sb-logo">{logo_h}</div>
      <div class="c-sb-nav">
        <div class="sb-sec">WORKSPACE</div>
        {nav}
        <div style="margin-top:auto;padding-top:16px">
          {user_html}
        </div>
      </div>
    </div>'''
    st.markdown(html, unsafe_allow_html=True)

    # 로그아웃 버튼 (Streamlit 네이티브)
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    if st.button("🚪 로그아웃", use_container_width=True, key="logout_btn"):
        _cookie_mgr.delete(TOKEN_COOKIE)
        st.session_state.authenticated = False
        st.session_state.auth_user     = {}
        st.rerun()

# ══════════════════════════════════════════════════════════════════════
#  Bottom nav (mobile)
# ══════════════════════════════════════════════════════════════════════
def render_bnav():
    items = [('dashboard','대시보드',I_DASH),('branch','지점',I_BRANCH),('upload','업로드',I_UP),('rules','규칙',I_RULE)]
    h = '<div class="bnav">'
    for p, lbl, ic in items:
        cls = 'on' if page == p else ''
        h += f'<a href="?page={p}" target="_self" class="{cls}">{ic}<span>{lbl}</span></a>'
    h += '</div>'
    st.markdown(h, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  KPI row
# ══════════════════════════════════════════════════════════════════════
def render_kpi(df):
    tot_rev  = df["총매출"].sum()
    card_rev = df["카드실수령"].sum()
    cash_rev = df["현금공급가액"].sum()
    tot_exp  = df["총지출"].sum()
    tot_pnl  = df["손익"].sum()
    rate     = round(tot_pnl/tot_rev*100, 1) if tot_rev else 0
    pc       = (df["손익"]>0).sum()
    tc       = len(df[df["총매출"]>0])
    sign_pnl = "▲" if tot_pnl >= 0 else "▼"
    sign_rt  = "+" if rate >= 0 else ""
    tc_cls   = "c-pos" if pc >= tc/2 else "c-red"

    cards = [
        ("카드 매출",  fw(card_rev), "원", f"공급가액 기준 실수령", "c-ink"),
        ("현금 매출",  fw(cash_rev), "원", f"입금 – 부가세", "c-ink"),
        ("총 지출",    fw(tot_exp),  "원", "인건비 + 부가세 + 기타", "c-red"),
        ("순 손익",    f"{sign_pnl} {fw(abs(tot_pnl))}", "원", "총매출 – 총지출", "c-pos" if tot_pnl>=0 else "c-red"),
        ("이익률",     f"{sign_rt}{rate}", "%", f"흑자 {pc} / {tc} 지점", "c-pos" if rate>=0 else "c-red"),
    ]
    html = '<div class="kpi-grid">'
    for lbl, val, unit, sub, cls in cards:
        html += f'<div class="kpi"><div class="kpi-lbl">{lbl}</div><div class="kpi-val {cls}">{val}<span class="kpi-unit">{unit}</span></div><div class="kpi-sub">{sub}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  Branch detail panel
# ══════════════════════════════════════════════════════════════════════
def render_detail(row, year, month):
    b     = row['branch']
    pnl   = int(row['손익'])
    rate  = row['이익률']
    pnl_cls  = "c-pos" if pnl >= 0 else "c-red"
    rate_bg  = "background:var(--poss);color:var(--pos)" if rate >= 0 else "background:var(--reds);color:var(--red)"
    sign  = "▲" if pnl >= 0 else "▼"

    # 카드 입금 = 공급가액 + VAT
    card_dep = int(row['카드공급가액']) + int(row['카드VAT'])

    # 현금 입금 = 공급가액 + VAT
    cash_dep = int(row['현금공급가액']) + int(row['현금VAT'])

    def dr(lbl, amt, cls='', sub=False):
        row_cls = "dp-row sub" if sub else "dp-row"
        lbl_cls = "dp-lbl" if not sub else "dp-lbl"
        amt_cls = f"dp-amt {cls}" if cls else "dp-amt"
        return f'<div class="{row_cls}"><span class="{lbl_cls}">{lbl}</span><span class="{amt_cls}">{fn(amt)}원</span></div>'

    # Expense detail from DB
    exp_df = c_exp(year, month)
    if not exp_df.empty:
        br_exp = exp_df[exp_df.branch == b]
        exp_by_cat = br_exp.groupby("category")["amount"].sum().to_dict()
    else:
        exp_by_cat = {}

    card_html = f"""
    <div class="dp-sec">
      <div class="dp-sec-t">카드 매출</div>
      {dr('공급가액', row['카드공급가액'], 'dp-lbl m')}
      {dr('부가세 (공급가액×10%)', row['카드VAT'], sub=True)}
      {dr('수수료', row['카드수수료'], sub=True)}
      <div class="dp-row tot"><span class="dp-lbl m">카드 실수령</span><span class="dp-amt c-ink">{fn(row['카드실수령'])}원</span></div>
    </div>"""

    cash_html = f"""
    <div class="dp-sec">
      <div class="dp-sec-t">현금 매출</div>
      {dr('입금액', cash_dep, 'dp-lbl m')}
      {dr('부가세', row['현금VAT'], sub=True)}
      <div class="dp-row tot"><span class="dp-lbl m">현금 공급가액</span><span class="dp-amt c-ink">{fn(row['현금공급가액'])}원</span></div>
    </div>"""

    pay_rows = ""
    pay_items = [("급여",row['급여']),("4대보험료",row['4대보험료']),
                 ("소득세·지방세",row['소득세지방세']),("프리랜서",row['프리랜서']),("프리랜서 세금",row['프리랜서세금'])]
    for lbl, amt in pay_items:
        if amt > 0: pay_rows += dr(lbl, amt, sub=True)

    other_rows = ""
    for cat, amt in sorted(exp_by_cat.items(), key=lambda x: -x[1]):
        if amt > 0: other_rows += dr(cat, amt, sub=True)

    exp_html = f"""
    <div class="dp-sec">
      <div class="dp-sec-t">지출 상세</div>
      {dr('인건비 합계', row['인건비합계'], 'dp-lbl m')}
      {pay_rows}
      {dr('기타지출 합계', row['기타지출'], 'dp-lbl m')}
      {other_rows}
      {dr('부가세 합계', row['부가세합계'], 'dp-lbl m')}
      <div class="dp-row tot"><span class="dp-lbl m">총 지출</span><span class="dp-amt c-red">{fn(row['총지출'])}원</span></div>
    </div>"""

    html = f"""
    <div class="dp">
      <div class="dp-hd">
        <span class="dp-title">{b} 상세</span>
        <div class="dp-profit">
          <span class="dp-profit-val {pnl_cls}">{sign} {fn(abs(pnl))}원</span>
          <span class="dp-profit-rate" style="{rate_bg}">{'+' if rate>=0 else ''}{rate}%</span>
        </div>
      </div>
      <div class="dp-cols">
        <div>{card_html}{cash_html}</div>
        <div>{exp_html}</div>
      </div>
    </div>"""
    st.markdown(html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  Branch chart
# ══════════════════════════════════════════════════════════════════════
def render_chart(df, key="ch"):
    dc = df[df["총매출"]>0].sort_values("총매출", ascending=False)
    if dc.empty:
        st.info("차트 데이터가 없습니다.")
        return
    fig = go.Figure()
    fig.add_trace(go.Bar(name="총매출", x=dc.branch, y=dc.총매출,
        marker_color="#3D3835", opacity=0.85,
        text=dc.총매출.apply(fw), textposition="outside",
        textfont=dict(size=10, color="#1F1B1B", family="Pretendard Variable,sans-serif")))
    fig.add_trace(go.Bar(name="총지출", x=dc.branch, y=dc.총지출,
        marker_color="#E60028", opacity=0.75))
    fig.add_trace(go.Scatter(name="손익", x=dc.branch, y=dc.손익,
        mode="lines+markers", yaxis="y2",
        line=dict(color="#2E7D5B", width=2.5),
        marker=dict(size=7, color=["#2E7D5B" if v>=0 else "#E60028" for v in dc.손익],
                    line=dict(width=2, color="white"))))
    _tf = dict(size=11, color="#1F1B1B", family="Pretendard Variable,sans-serif")
    layout = {**PLOT_BASE, "barmode":"group", "height":380,
        "yaxis":  dict(tickformat=",", gridcolor="rgba(31,27,27,.08)", zeroline=False,
                       tickfont=_tf, color="#1F1B1B"),
        "yaxis2": dict(overlaying="y", side="right", tickformat=",",
                       zeroline=True, zerolinecolor="rgba(31,27,27,.2)",
                       tickfont=_tf, color="#1F1B1B"),
        "xaxis":  dict(tickangle=-30, tickfont=_tf, color="#1F1B1B"),
        "margin": dict(t=16, b=70, l=10, r=10)}
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, key=key)

def render_rank_cards(df):
    active = df[df["총매출"] > 0].sort_values("손익", ascending=False)
    if active.empty:
        st.info("데이터 없음")
        return
    top3    = active.head(3)
    bottom3 = active.tail(3).sort_values("손익")

    def card_row(row, rank, is_top):
        pnl  = int(row["손익"])
        rate = row["이익률"]
        sign = "▲" if pnl >= 0 else "▼"
        if is_top:
            pnl_col  = "var(--pos)";  bg = "var(--poss)"; rate_col = "var(--pos)"
        else:
            pnl_col  = "var(--red)";  bg = "var(--reds)"; rate_col = "var(--red)"
        rate_sign = "+" if rate >= 0 else ""
        return f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
          padding:10px 14px;border-radius:var(--rs);background:{bg};margin-bottom:6px">
          <div style="display:flex;align-items:center;gap:10px">
            <span style="font-size:12px;font-weight:800;color:{pnl_col};
              width:18px;text-align:center">{rank}</span>
            <span style="font-size:13px;font-weight:600;color:var(--ink)">{row['branch']}</span>
          </div>
          <div style="text-align:right">
            <div style="font-size:13px;font-weight:700;color:{pnl_col}">
              {sign} {fw(abs(pnl))}</div>
            <div style="font-size:11px;font-weight:600;color:{rate_col}">
              {rate_sign}{rate:.1f}%</div>
          </div>
        </div>"""

    html = '<div style="display:flex;flex-direction:column;gap:16px">'
    # 상위 3
    html += '<div><div style="font-size:10px;font-weight:700;color:var(--pos);letter-spacing:.07em;text-transform:uppercase;margin-bottom:8px">🏆 흑자 TOP 3</div>'
    for i, (_, row) in enumerate(top3.iterrows()):
        html += card_row(row, i+1, True)
    html += '</div>'
    # 하위 3
    html += '<div><div style="font-size:10px;font-weight:700;color:var(--red);letter-spacing:.07em;text-transform:uppercase;margin-bottom:8px">⚠️ 적자 BOTTOM 3</div>'
    for i, (_, row) in enumerate(bottom3.iterrows()):
        html += card_row(row, i+1, False)
    html += '</div></div>'
    st.markdown(html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  PDF generator (HTML)
# ══════════════════════════════════════════════════════════════════════
def gen_pdf_html(df, branches, year, month, exp_df=None):
    # 인건비 카테고리 (기타지출에서 제외)
    payroll_cats = {"급여","4대보험료","소득세·지방세 합계","프리랜서","퇴직금","소득세지방세"}

    rows_html = ""
    for _, row in df[df.branch.isin(branches)].iterrows():
        b = row.branch
        pnl = int(row['손익'])
        rt  = row['이익률']
        pnl_col = "#2E7D5B" if pnl>=0 else "#E60028"
        sign = "▲" if pnl>=0 else "▼"

        # 기타지출 카테고리별 상세
        other_rows_html = ""
        if exp_df is not None and not exp_df.empty:
            br_exp = exp_df[(exp_df.branch == b) & (~exp_df.category.isin(payroll_cats))]
            cat_sums = br_exp.groupby("category")["amount"].sum().sort_values(ascending=False)
            for cat, amt in cat_sums.items():
                if amt > 0:
                    other_rows_html += f'<tr class="sub"><td>&nbsp;&nbsp;{cat}</td><td class="amt">{fn(amt)} 원</td></tr>'
        if not other_rows_html:
            other_rows_html = f'<tr class="sub"><td>&nbsp;&nbsp;기타지출 합계</td><td class="amt">{fn(row["기타지출"])} 원</td></tr>'

        rows_html += f"""
        <div class="branch-block">
          <div class="branch-title">{b}</div>
          <table>
            <tr class="sec-head"><th colspan="2">[ 매출 ]</th></tr>
            <tr><td>카드 공급가액</td><td class="amt">{fn(row['카드공급가액'])} 원</td></tr>
            <tr class="sub"><td>&nbsp;&nbsp;카드 부가세</td><td class="amt">{fn(row['카드VAT'])} 원</td></tr>
            <tr class="sub"><td>&nbsp;&nbsp;카드 수수료</td><td class="amt">{fn(row['카드수수료'])} 원</td></tr>
            <tr class="bold"><td>카드 실수령</td><td class="amt">{fn(row['카드실수령'])} 원</td></tr>
            <tr><td>현금 공급가액</td><td class="amt">{fn(row['현금공급가액'])} 원</td></tr>
            <tr class="sub"><td>&nbsp;&nbsp;현금 부가세</td><td class="amt">{fn(row['현금VAT'])} 원</td></tr>
            <tr class="bold total"><td>총 매출</td><td class="amt">{fn(row['총매출'])} 원</td></tr>
            <tr class="sec-head"><th colspan="2">[ 인건비 ]</th></tr>
            <tr class="sub"><td>&nbsp;&nbsp;급여</td><td class="amt">{fn(row['급여'])} 원</td></tr>
            <tr class="sub"><td>&nbsp;&nbsp;4대보험료</td><td class="amt">{fn(row['4대보험료'])} 원</td></tr>
            <tr class="sub"><td>&nbsp;&nbsp;소득세·지방세</td><td class="amt">{fn(row['소득세지방세'])} 원</td></tr>
            <tr class="sub"><td>&nbsp;&nbsp;프리랜서</td><td class="amt">{fn(row['프리랜서'])} 원</td></tr>
            <tr class="sub"><td>&nbsp;&nbsp;프리랜서 세금</td><td class="amt">{fn(row['프리랜서세금'])} 원</td></tr>
            <tr class="bold"><td>인건비 합계</td><td class="amt">{fn(row['인건비합계'])} 원</td></tr>
            <tr class="sec-head"><th colspan="2">[ 기타지출 ]</th></tr>
            {other_rows_html}
            <tr class="bold"><td>기타지출 합계</td><td class="amt">{fn(row['기타지출'])} 원</td></tr>
            <tr class="sec-head"><th colspan="2">[ 부가세 ]</th></tr>
            <tr class="sub"><td>&nbsp;&nbsp;카드 VAT</td><td class="amt">{fn(row['카드VAT'])} 원</td></tr>
            <tr class="sub"><td>&nbsp;&nbsp;현금 VAT</td><td class="amt">{fn(row['현금VAT'])} 원</td></tr>
            <tr class="bold"><td>부가세 합계</td><td class="amt">{fn(row['부가세합계'])} 원</td></tr>
            <tr class="bold total"><td>총 지출</td><td class="amt">{fn(row['총지출'])} 원</td></tr>
            <tr class="result"><td>순 손익</td><td class="amt" style="color:{pnl_col}">{sign} {fn(abs(pnl))} 원</td></tr>
            <tr class="result"><td>이익률</td><td class="amt" style="color:{pnl_col}">{('+' if rt>=0 else '')}{rt}%</td></tr>
          </table>
        </div>"""

    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
    <title>정산 보고서 {year}년 {month}월</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
    <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Pretendard Variable',sans-serif;background:#FAF7F5;color:#1F1B1B;padding:40px}}
    .report-header{{margin-bottom:32px;padding-bottom:20px;border-bottom:2px solid #E60028}}
    .report-header h1{{font-size:24px;font-weight:800;letter-spacing:-.02em}}
    .report-header p{{font-size:13px;color:#9A918C;margin-top:6px}}
    .branch-block{{background:#fff;border:1px solid rgba(31,27,27,.09);border-radius:12px;
      padding:20px;margin-bottom:20px;page-break-inside:avoid}}
    .branch-title{{font-size:16px;font-weight:700;margin-bottom:14px;padding-bottom:10px;
      border-bottom:1px solid rgba(31,27,27,.09);color:#1F1B1B}}
    table{{width:100%;border-collapse:collapse;font-size:13px}}
    td{{padding:7px 4px;border-bottom:1px solid rgba(31,27,27,.06)}}
    td:last-child{{text-align:right}}
    .amt{{font-feature-settings:'tnum' 1;font-weight:500}}
    .sec-head th{{padding:10px 4px 6px;font-size:10.5px;color:#9A918C;font-weight:700;
      text-transform:uppercase;letter-spacing:.05em;text-align:left}}
    .sub td{{padding:5px 4px 5px;color:#5B5450;font-size:12px}}
    .bold td{{font-weight:700}}
    .total td{{border-top:1px solid rgba(31,27,27,.15);padding:10px 4px}}
    .result td{{font-size:14px;font-weight:700;padding:10px 4px;border-top:2px solid rgba(31,27,27,.1)}}
    @media print{{body{{padding:20px}}@page{{margin:15mm}}}}
    </style></head><body>
    <div class="report-header">
      <h1>정산 보고서</h1>
      <p>{year}년 {month}월 · 라온스포츠 · 선택 지점 {len(branches)}개 · 브라우저에서 인쇄(Ctrl+P) → PDF로 저장</p>
    </div>
    {rows_html}
    </body></html>"""

# ══════════════════════════════════════════════════════════════════════
#  Render nav
# ══════════════════════════════════════════════════════════════════════
render_sidebar()
render_bnav()
# Mobile-only logo header (top-center, hidden on PC via CSS)
st.markdown(f'<div class="mob-hd">{get_logo_html(mobile=True)}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  1. DASHBOARD
# ══════════════════════════════════════════════════════════════════════
if page == 'dashboard':
    year  = st.session_state.year
    month = st.session_state.month
    sel   = st.session_state.sel_br

    # Mobile: inline filters (sidebar hidden on mobile)
    st.markdown('<div class="ph"><div class="ph-title">대시보드</div><div class="ph-sub">연도 · 월 · 지점을 선택하면 데이터가 필터링됩니다</div></div>', unsafe_allow_html=True)

    # Inline filter bar (always visible, PC & Mobile)
    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 2])
    yrs = list(range(_now.year, _now.year - 3, -1))
    year  = c1.selectbox("연도", yrs, index=yrs.index(year) if year in yrs else 0, key="f_yr")
    month = c2.selectbox("월", list(range(1,13)), index=month-1, key="f_mn", format_func=lambda m: f"{m}월")
    sel   = c3.selectbox("지점", ['전체']+BRANCH_LIST, key="f_br")
    st.session_state.year  = year
    st.session_state.month = month
    st.session_state.sel_br = sel
    st.markdown('</div>', unsafe_allow_html=True)

    # Load data
    with st.spinner("데이터 로드 중..."):
        full_df = build_summary(year, month)

    # Filter by branch if selected
    if sel != '전체':
        view_df = full_df[full_df.branch == sel]
    else:
        view_df = full_df

    # KPI
    render_kpi(view_df)

    # ── 보기 방식 토글 ──
    sec(f"{year}년 {month}월 · {'전체 지점' if sel=='전체' else sel}")
    view_mode = st.radio("보기 방식", ["요약", "상세"], horizontal=True, key="tbl_mode")

    if view_mode == "상세":
        # ── 상세 표 (전체 계정과목) ──
        detail_cols = {
            "branch":       "지점",
            "카드공급가액": "카드공급가액",
            "카드수수료":   "카드수수료",
            "카드VAT":      "카드VAT",
            "카드실수령":   "카드실수령",
            "현금공급가액": "현금공급가액",
            "현금VAT":      "현금VAT",
            "총매출":       "총매출",
            "급여":         "급여",
            "4대보험료":    "4대보험료",
            "소득세지방세": "소득세·지방세",
            "프리랜서":     "프리랜서",
            "프리랜서세금": "프리랜서세금",
            "인건비합계":   "인건비합계",
            "기타지출":     "기타지출",
            "부가세합계":   "부가세합계",
            "총지출":       "총지출",
            "손익":         "손익",
            "이익률":       "이익률(%)",
        }
        disp = view_df[[c for c in detail_cols if c in view_df.columns]].copy()
        disp = disp.rename(columns=detail_cols)

        def _color_pnl(val):
            try:
                v = float(str(val).replace(",",""))
                if v > 0: return "color:#2E7D5B;font-weight:700"
                if v < 0: return "color:#E60028;font-weight:700"
            except: pass
            return ""

        int_cols_det = [c for c in disp.columns if c not in ("지점","이익률(%)")]
        for c in int_cols_det:
            disp[c] = disp[c].apply(lambda v: f"{int(v):,}" if pd.notna(v) else "0")
        disp["이익률(%)"] = disp["이익률(%)"].apply(lambda v: f"{float(v):.1f}%" if pd.notna(v) else "0%")

        st.dataframe(
            disp.style
                .map(_color_pnl, subset=["손익"])
                .set_properties(**{"text-align":"right"}, subset=int_cols_det)
                .set_properties(**{"font-weight":"700","text-align":"left"}, subset=["지점"]),
            use_container_width=True, hide_index=True, height=600
        )

    else:
        # ── 요약 표 (<table> 구조로 완벽한 열 정렬) ──
        table_html = '''<div class="bt"><table>
<thead><tr>
  <th style="text-align:left">지점</th>
  <th>카드매출</th>
  <th>현금매출</th>
  <th>총지출</th>
  <th>손익 / 이익률</th>
</tr></thead><tbody>'''

        for _, row in view_df.iterrows():
            b   = row.branch
            pnl = int(row['손익'])
            rt  = row['이익률']
            sel_cls = "sel" if st.session_state.drill == b else ""
            sign    = "▲" if pnl >= 0 else "▼"
            bdg_cls = "bdg-pos" if pnl >= 0 else "bdg-neg"
            rate_col = "color:var(--pos)" if rt >= 0 else "color:var(--red)"
            table_html += f'''<tr class="{sel_cls}">
  <td>{b}</td>
  <td>{fw(row["카드실수령"])}</td>
  <td>{fw(row["현금공급가액"])}</td>
  <td>{fw(row["총지출"])}</td>
  <td style="text-align:center"><span class="bdg {bdg_cls}">{sign} {fw(abs(pnl))}</span>&nbsp;<span style="font-size:11.5px;{rate_col}">{("+" if rt>=0 else "")}{rt}%</span></td>
</tr>'''

        table_html += '</tbody></table></div>'
        st.markdown(table_html, unsafe_allow_html=True)

    # Charts
    sec("지점별 매출 · 지출 · 손익")
    col_ch1, col_ch2 = st.columns([3, 2])
    with col_ch1:
        st.markdown('<div class="ch"><div class="ch-t">매출 · 지출 비교</div><div class="ch-s">막대: 매출/지출 &nbsp;|&nbsp; 선: 손익 (우축)</div>', unsafe_allow_html=True)
        render_chart(view_df, key="ch_main")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_ch2:
        st.markdown('<div class="ch"><div class="ch-t">손익 순위</div><div class="ch-s">흑자 TOP3 · 적자 BOTTOM3</div>', unsafe_allow_html=True)
        render_rank_cards(view_df)
        st.markdown('</div>', unsafe_allow_html=True)

    # PDF Section
    sec("정산서 내보내기")

    # 지점 선택 (카드 바깥)
    chk_all = st.checkbox("전체 지점 선택", value=True, key="pdf_all")
    if chk_all:
        pdf_branches = view_df[view_df.총매출>0].branch.tolist()
    else:
        available = view_df[view_df.총매출>0].branch.tolist()
        rows_c = [st.columns(4) for _ in range((len(available)+3)//4)]
        flat   = [c for row_c in rows_c for c in row_c]
        pdf_branches = [b for b, col in zip(available, flat) if col.checkbox(b, value=True, key=f"pdf_{b}")]

    # 카드 안에 타이틀 + 버튼 (순수 HTML 카드 — base64 다운로드)
    import base64
    if pdf_branches:
        exp_df_pdf   = c_exp(year, month)
        html_content = gen_pdf_html(full_df, pdf_branches, year, month, exp_df=exp_df_pdf)
        html_b64     = base64.b64encode(html_content.encode("utf-8")).decode()
        btn_part = f'<a href="data:text/html;base64,{html_b64}" download="정산보고서_{year}년{month}월.html" style="background:#E53935;color:#fff;border-radius:8px;font-weight:600;font-size:14px;padding:10px 22px;text-decoration:none;white-space:nowrap;display:inline-block;box-shadow:0 2px 6px rgba(229,57,53,.35)">정산서 다운로드</a>'
    else:
        btn_part = '<span style="background:#ccc;color:#fff;border-radius:8px;font-weight:600;font-size:14px;padding:10px 22px;white-space:nowrap;display:inline-block;cursor:not-allowed">정산서 다운로드</span>'

    card_html = f'<div class="pdf-box" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px"><div><div class="pdf-t" style="margin-bottom:6px">📄 정산서 다운로드</div><div style="font-size:12px;color:#888">다운로드 후 브라우저에서 열고 Ctrl+P → PDF 저장</div></div>{btn_part}</div>'
    st.markdown(card_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  2. BRANCH DETAIL
# ══════════════════════════════════════════════════════════════════════
elif page == 'branch':
    year  = st.session_state.year
    month = st.session_state.month

    st.markdown('<div class="ph"><div class="ph-title">지점 상세 내역</div><div class="ph-sub">지점을 선택하면 매출·지출 상세 내역을 확인합니다</div></div>', unsafe_allow_html=True)

    # 필터
    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns([1, 1, 2])
    yrs   = list(range(_now.year, _now.year - 3, -1))
    year  = fc1.selectbox("연도", yrs, index=yrs.index(year) if year in yrs else 0, key="br_yr")
    month = fc2.selectbox("월", list(range(1,13)), index=month-1, key="br_mn", format_func=lambda m: f"{m}월")
    br_sel = fc3.selectbox("지점 선택", BRANCH_LIST, key="br_sel")
    st.session_state.year  = year
    st.session_state.month = month
    st.markdown('</div>', unsafe_allow_html=True)

    with st.spinner("데이터 로드 중..."):
        full_df = build_summary(year, month)

    br_row = full_df[full_df.branch == br_sel]
    if br_row.empty or br_row.iloc[0]["총매출"] == 0:
        st.markdown('<div class="al al-warn">⚠️&nbsp; 해당 지점의 데이터가 없습니다.</div>', unsafe_allow_html=True)
    else:
        render_detail(br_row.iloc[0], year, month)

        # 월별 추이 차트
        sec("월별 손익 추이")
        months_data = []
        for m in range(1, 13):
            r = build_summary(year, m)
            row = r[r.branch == br_sel]
            if not row.empty:
                months_data.append({"월": f"{m}월", "총매출": row.iloc[0]["총매출"],
                                    "총지출": row.iloc[0]["총지출"], "손익": row.iloc[0]["손익"]})
            else:
                months_data.append({"월": f"{m}월", "총매출": 0, "총지출": 0, "손익": 0})
        mdf = pd.DataFrame(months_data)
        fig_br = go.Figure()
        fig_br.add_trace(go.Bar(name="총매출", x=mdf["월"], y=mdf["총매출"],
            marker_color="#3D3835", opacity=0.8))
        fig_br.add_trace(go.Bar(name="총지출", x=mdf["월"], y=mdf["총지출"],
            marker_color="#E60028", opacity=0.75))
        fig_br.add_trace(go.Scatter(name="손익", x=mdf["월"], y=mdf["손익"],
            mode="lines+markers", yaxis="y2",
            line=dict(color="#2E7D5B", width=2.5),
            marker=dict(size=8, color=["#2E7D5B" if v>=0 else "#E60028" for v in mdf["손익"]],
                        line=dict(width=2, color="white"))))
        fig_br.update_layout(**{**PLOT_BASE, "barmode":"group", "height":320,
            "yaxis":  dict(tickformat=",", gridcolor="rgba(31,27,27,.08)", zeroline=False),
            "yaxis2": dict(overlaying="y", side="right", tickformat=",",
                           zeroline=True, zerolinecolor="rgba(31,27,27,.2)"),
            "xaxis":  dict(tickfont=dict(size=11))})
        st.plotly_chart(fig_br, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
#  3. UPLOAD
# ══════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════
#  4. UPLOAD  (formerly 2)
# ══════════════════════════════════════════════════════════════════════
elif page == 'upload':
    st.markdown('<div class="ph"><div class="ph-title">데이터 업로드</div><div class="ph-sub">엑셀 파일을 업로드하면 자동으로 파싱·저장됩니다</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="al al-info">ℹ️&nbsp; 같은 연월을 다시 올리면 기존 데이터가 교체됩니다. 업로드 전 백업을 권장합니다.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["카드 매출", "통장 내역", "인건비"])

    with tab1:
        st.subheader("카드 매출 업로드")
        c1, c2 = st.columns(2)
        uy = c1.number_input("연도", value=_now.year, min_value=2020, max_value=2030, key="uy")
        um = c2.selectbox("월", list(range(1,13)), index=_now.month-1, key="um", format_func=lambda m: f"{m}월")

        sec("① 카드사 결과 집계 조회")
        f1 = st.file_uploader("카드사 결과 집계 조회.xlsx", type=["xlsx"], key="agg")
        if f1 and st.button("저장", key="b_agg"):
            with st.spinner("처리 중..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(f1.read()); tp = tmp.name
                try:
                    df = parse_card_aggregate(tp, uy, um)
                    upsert_card_sales(df, "card_aggregate", uy, um)
                    st.cache_data.clear()
                    un = (df.branch=="미매핑").sum()
                    st.success(f"✅ {len(df)}건 저장 완료 (미매핑 {un}건)")
                    if un: st.dataframe(df[df.branch=="미매핑"][["raw_merchant","total_amount"]])
                except Exception as e:
                    st.error(f"❌ 오류: {e}")
                finally: os.unlink(tp)

        sec("② 신용카드")
        f2 = st.file_uploader("신용카드.xlsx", type=["xlsx"], key="cc")
        if f2 and st.button("저장", key="b_cc"):
            with st.spinner("처리 중..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(f2.read()); tp = tmp.name
                try:
                    df = parse_credit_card(tp, uy, um)
                    upsert_card_sales(df, "credit_card", uy, um)
                    st.cache_data.clear()
                    st.success(f"✅ {len(df)}건 저장 완료")
                except Exception as e:
                    st.error(f"❌ 오류: {e}")
                finally: os.unlink(tp)

    with tab2:
        st.subheader("통장 내역 업로드")
        c1, c2 = st.columns(2)
        by = c1.number_input("연도", value=_now.year, min_value=2020, max_value=2030, key="by")
        bm = c2.selectbox("월", list(range(1,13)), index=_now.month-1, key="bm", format_func=lambda m: f"{m}월")
        st.caption("💡 하나통장(여러 시트)과 신한통장이 합쳐진 파일을 그대로 업로드하세요. 자동으로 감지합니다.")
        fb = st.file_uploader("통장내역.xlsx", type=["xlsx"], key="bank")

        # ── 파일 올라오면 시트 구조 즉시 표시 (저장 전 확인용) ──
        if fb:
            _xl_check = pd.ExcelFile(fb)
            with st.expander(f"📋 파일 구조 확인 ({len(_xl_check.sheet_names)}개 시트)", expanded=True):
                for _sn in _xl_check.sheet_names:
                    try:
                        _raw = _xl_check.parse(_sn, header=None, nrows=4, dtype=str)
                        # 헤더 후보 행 출력
                        _hrow = 0
                        for _ri, _row in _raw.iterrows():
                            _vals = [str(v).strip() for v in _row if pd.notna(v) and str(v).strip() not in ("nan","")]
                            if "No" in _vals:
                                _hrow = _ri
                                break
                        _headers = [str(v).strip() for v in _raw.iloc[_hrow] if pd.notna(v) and str(v).strip() not in ("nan","")]
                        # 판별 결과
                        if any("전체선택" in v for v in _headers):
                            _kind = "🟦 신한통장"
                        elif any("의뢰인" in v or "수취인" in v for v in _headers):
                            _kind = "🟩 하나통장"
                        else:
                            _kind = "❓ 미감지"
                        st.markdown(f"**{_sn}** → {_kind}")
                        st.caption("헤더: " + " | ".join(_headers[:10]))
                    except Exception as _e:
                        st.caption(f"{_sn}: 읽기 실패 ({_e})")

        if fb and st.button("저장", type="primary", key="b_bank"):
            with st.spinner("시트 자동 감지 및 분류 중..."):
                xl = pd.ExcelFile(fb)
                bank_data = parse_bank_auto(xl, by, bm)
                saved = False
                bank_names = {"hana": "하나통장", "shinhan": "신한통장"}
                for bank, df in bank_data.items():
                    if df.empty:
                        continue
                    try:
                        # 1) 키워드 규칙 + 스마트 분류
                        df = classify_transactions(df, bank)
                        # 2) AI fallback — 키워드·스마트 분류 모두 실패한 항목만
                        if _api_key:
                            unclf = df[df["needs_review"] == 1]
                            if not unclf.empty:
                                tx_list = unclf[["description","counterpart","deposit","withdrawal"]].to_dict("records")
                                ai_res  = ai_classify_batch(tx_list, BRANCH_LIST, ALL_CATEGORIES, _api_key)
                                for item in ai_res:
                                    try:
                                        loc_idx = unclf.index[item["id"]]
                                        br  = item.get("branch", "")
                                        cat = item.get("category", "")
                                        conf = float(item.get("confidence", 0))
                                        if br or cat:
                                            df.at[loc_idx, "branch"]   = br
                                            df.at[loc_idx, "category"] = cat
                                            df.at[loc_idx, "classification_source"] = "ai"
                                            df.at[loc_idx, "is_excluded"] = 1 if cat == "제외" else 0
                                            # 확신도 75% 이상이고 지점·계정과목 모두 있으면 자동 확정
                                            if conf >= 0.75 and br and cat:
                                                df.at[loc_idx, "needs_review"] = 0
                                    except Exception:
                                        pass
                        # 3) VAT 재계산
                        df = recalc_vat(df)
                        # 4) DB 저장
                        upsert_bank_transactions(df, bank, by, bm)
                        total    = len(df)
                        auto_ok  = int((df.needs_review == 0).sum())
                        need_rev = int(df.needs_review.sum())
                        ai_cnt   = int((df.get("classification_source", "") == "ai").sum()) if "classification_source" in df.columns else 0
                        st.success(
                            f"✅ {bank_names[bank]}: 총 {total}건 저장 "
                            f"(자동분류 {auto_ok}건 / AI {ai_cnt}건 / 미분류 {need_rev}건)"
                        )
                        saved = True
                    except Exception as e:
                        st.error(f"❌ {bank_names[bank]} 저장 실패: {e}")
                if not saved:
                    st.warning("⚠️ 하나·신한 통장 시트를 찾지 못했습니다. 파일을 확인해주세요.")
                else:
                    if any(not bank_data[b].empty for b in bank_data):
                        need_total = sum(
                            int(df.needs_review.sum())
                            for df in bank_data.values() if not df.empty
                        )
                        if need_total > 0:
                            st.info(f"📋 미분류 {need_total}건은 '규칙 관리 → 계정과목 검토' 메뉴에서 확인하세요.")
                    st.cache_data.clear()

    with tab3:
        st.subheader("인건비 업로드")
        c1, c2 = st.columns(2)
        py = c1.number_input("연도", value=_now.year, min_value=2020, max_value=2030, key="py")
        pm = c2.selectbox("월", list(range(1,13)), index=_now.month-1, key="pm", format_func=lambda m: f"{m}월")
        fp = st.file_uploader("지점별 대시보드.xlsx", type=["xlsx"], key="pay")
        if fp and st.button("저장", type="primary", key="b_pay"):
            with st.spinner("처리 중..."):
                xl2 = pd.ExcelFile(fp)
                saved_pay = False
                for fn_parse, typ, lbl in [(parse_payroll_freelance,"freelance","프리랜서"), (parse_payroll_insured,"insured","4대보험")]:
                    try:
                        df = fn_parse(xl2, py, pm)
                        upsert_payroll(df, py, pm, typ)
                        st.success(f"✅ {lbl}: {len(df)}개 지점")
                        saved_pay = True
                    except Exception as e:
                        st.error(f"❌ {lbl}: {e}")
                if saved_pay:
                    st.cache_data.clear()

# ══════════════════════════════════════════════════════════════════════
#  3. RULES
# ══════════════════════════════════════════════════════════════════════
elif page == 'rules':
    st.markdown('<div class="ph"><div class="ph-title">규칙 관리</div><div class="ph-sub">계정과목 검토 및 키워드 자동분류 규칙</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["계정과목 검토", "규칙 목록 · 추가", "⚙️ AI 설정"])

    # ── 탭1: 계정과목 검토 ─────────────────────────────────
    with tab1:
        # 필터 행 1: 연도 / 월 / 통장
        _yr_list = list(range(2024, _now.year + 2))
        fa1, fa2, fa3 = st.columns([1, 1, 1])
        rv_year  = fa1.selectbox("연도", _yr_list, index=_yr_list.index(_now.year) if _now.year in _yr_list else len(_yr_list)-1, key="rv_year")
        rv_month = fa2.selectbox("월", list(range(1, 13)), index=_now.month-1, key="rv_month", format_func=lambda m: f"{m}월")
        rv_bank  = fa3.selectbox("통장", ["전체", "hana", "신한(shinhan)"], key="rv_bank")

        # 필터 행 2: 지점 / 계정과목 / 상태
        bank_filter = None if rv_bank == "전체" else ("shinhan" if "신한" in rv_bank else "hana")
        rv_df_all   = get_all_bank_transactions(rv_year, rv_month, bank_filter)

        fb1, fb2, fb3 = st.columns([1, 1, 1])
        # 실제 데이터에 있는 지점 목록만 표시
        exist_branches   = ["전체"] + sorted([b for b in (rv_df_all["branch"].dropna().unique().tolist() if not rv_df_all.empty else []) if b])
        exist_categories = ["전체"] + sorted([c for c in (rv_df_all["category"].dropna().unique().tolist() if not rv_df_all.empty else []) if c])
        rv_branch   = fb1.selectbox("지점", exist_branches, key="rv_branch")
        rv_category = fb2.selectbox("계정과목", exist_categories, key="rv_category")
        rv_status   = fb3.selectbox("상태", ["전체", "미분류만", "AI분류", "자동분류", "제외"], key="rv_status")

        # 필터 적용
        rv_df = rv_df_all.copy() if not rv_df_all.empty else rv_df_all
        if not rv_df.empty:
            if rv_branch != "전체":
                rv_df = rv_df[rv_df["branch"] == rv_branch]
            if rv_category != "전체":
                rv_df = rv_df[rv_df["category"] == rv_category]
            if rv_status == "미분류만":
                rv_df = rv_df[rv_df["needs_review"] == 1]
            elif rv_status == "AI분류":
                rv_df = rv_df[rv_df.get("classification_source", "") == "ai"] if "classification_source" in rv_df.columns else rv_df
            elif rv_status == "자동분류":
                rv_df = rv_df[rv_df.get("classification_source", "").isin(["rule","smart"])] if "classification_source" in rv_df.columns else rv_df
            elif rv_status == "제외":
                rv_df = rv_df[rv_df["is_excluded"] == 1] if "is_excluded" in rv_df.columns else rv_df

        if rv_df_all.empty:
            st.markdown('<div class="al al-ok">✅&nbsp; 해당 월의 거래 내역이 없습니다.</div>', unsafe_allow_html=True)
        else:
            total = len(rv_df)
            unrev = int(rv_df_all["needs_review"].sum()) if "needs_review" in rv_df_all.columns else 0
            ai_cnt = int((rv_df_all.get("classification_source","") == "ai").sum()) if "classification_source" in rv_df_all.columns else 0

            # AI 일괄분류 버튼
            ai_col1, ai_col2 = st.columns([3, 1])
            ai_col1.caption(f"표시 {total}건 · 전체 미분류 {unrev}건 · AI분류 {ai_cnt}건")
            if _api_key:
                if unrev > 0 and ai_col2.button("🤖 AI 일괄분류", type="primary", key="ai_bulk"):
                    unclf_rows = rv_df_all[rv_df_all["needs_review"] == 1]
                    tx_list = unclf_rows[["description","counterpart","deposit","withdrawal"]].to_dict("records")
                    with st.spinner(f"🤖 AI가 {len(tx_list)}건 분류 중..."):
                        ai_res = ai_classify_batch(tx_list, BRANCH_LIST, ALL_CATEGORIES, _api_key)
                    applied = 0
                    for item in ai_res:
                        try:
                            loc_idx = unclf_rows.index[item["id"]]
                            tx_id   = int(rv_df_all.loc[loc_idx, "id"])
                            br      = item.get("branch", "")
                            cat     = item.get("category", "제외" if not item.get("branch") else "")
                            conf    = float(item.get("confidence", 0))
                            if cat:
                                needs_rv = 0 if (conf >= 0.75 and br and cat) else 1
                                update_transaction_classification(tx_id, br or "본사", cat, "ai")
                                applied += 1
                        except Exception:
                            pass
                    st.success(f"✅ {applied}건 AI 분류 완료!")
                    st.cache_data.clear()
                    st.rerun()
            else:
                ai_col2.caption("🔑 API 키 없음")

            st.divider()

            # 상태 뱃지
            def _status_badge(row):
                src = str(row.get("classification_source", "") or "")
                if row.get("is_excluded", 0) == 1:
                    return "⛔ 제외"
                if src == "rule":
                    return "✅ 자동"
                if src == "smart":
                    return "🔵 스마트"
                if src == "ai":
                    return "🤖 AI"
                if src == "manual":
                    return "✏️ 수동"
                if row.get("needs_review", 0) == 1:
                    return "❓ 미분류"
                return "✅ 분류됨"

            # 거래 목록
            for _, row in rv_df.iterrows():
                amt      = int(row.get("deposit", 0) or 0) or int(row.get("withdrawal", 0) or 0)
                tp       = "입금" if int(row.get("deposit", 0) or 0) > 0 else "출금"
                badge    = _status_badge(row)
                bank_lbl = str(row.get("bank", "")).upper()
                date_lbl = str(row.get("tx_date", ""))[:10]
                desc_lbl = str(row.get("description", ""))[:30]
                lbl = f"{badge}  [{bank_lbl}] {date_lbl}  ·  {desc_lbl}  ·  {tp} {amt:,}원"

                with st.expander(lbl, expanded=(row.get("needs_review", 0) == 1)):
                    cur_branch  = str(row.get("branch", "") or "")
                    cur_cat     = str(row.get("category", "") or "")
                    counterpart = str(row.get("counterpart", "") or "")
                    content     = str(row.get("content", "") or "")

                    if counterpart or content:
                        st.caption(f"의뢰인/수취인: {counterpart}  |  내용: {content}")

                    ci1, ci2, ci3, ci4 = st.columns([2, 2, 1, 1])

                    br_idx  = BRANCH_LIST.index(cur_branch) if cur_branch in BRANCH_LIST else 0
                    new_br  = ci1.selectbox("지점", BRANCH_LIST, index=br_idx, key=f"rv_br_{row.id}")
                    cat_opts = [""] + ALL_CATEGORIES
                    cat_idx  = cat_opts.index(cur_cat) if cur_cat in cat_opts else 0
                    new_ct  = ci2.selectbox("계정과목", cat_opts, index=cat_idx, key=f"rv_ct_{row.id}")

                    if ci3.button("저장", key=f"rv_sv_{row.id}", type="primary"):
                        if new_br and new_ct:
                            # 아이디어 2: AI 핵심 키워드 추출 후 규칙 저장
                            kw = ai_extract_keyword(
                                str(row.get("description","")),
                                counterpart, new_br, new_ct, _api_key
                            ) if _api_key else str(row.get("description",""))
                            update_transaction_classification(int(row.id), new_br, new_ct, "manual")
                            add_rule(str(row.bank), kw, new_br, new_ct)
                            st.success(f"저장 완료! (규칙 키워드: '{kw}')")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("지점과 계정과목을 모두 선택하세요.")

                    if ci4.button("제외", key=f"rv_ex_{row.id}"):
                        kw_ex = ai_extract_keyword(
                            str(row.get("description","")),
                            counterpart, cur_branch or "본사", "제외", _api_key
                        ) if _api_key else str(row.get("description",""))
                        update_transaction_classification(int(row.id), cur_branch or "본사", "제외", "manual")
                        add_rule(str(row.bank), kw_ex, cur_branch or "본사", "제외")
                        st.rerun()

    # ── 탭2: 규칙 목록 · 추가 ──────────────────────────────
    with tab2:
        sec("규칙 목록")
        bf = st.selectbox("통장", ["전체", "hana", "shinhan"])
        rdf = get_keyword_rules(None if bf == "전체" else bf)
        st.dataframe(rdf, use_container_width=True)
        st.caption(f"총 {len(rdf)}개 규칙")

        sec("새 규칙 추가")
        c1, c2 = st.columns(2)
        nb = c1.selectbox("통장", ["hana", "shinhan"], key="nb")
        nk = c2.text_input("키워드 (적요에 포함된 문자)")
        c3, c4 = st.columns(2)
        nbr = c3.selectbox("지점", BRANCH_LIST, key="nbr")
        nct = c4.selectbox("계정과목", ALL_CATEGORIES, key="nct")
        if st.button("규칙 추가", type="primary"):
            if nk:
                add_rule(nb, nk, nbr, nct)
                st.success(f"✅ [{nb}] '{nk}' → {nbr} / {nct}")
            else:
                st.error("키워드를 입력하세요.")

    # ── 탭3: AI 설정 ───────────────────────────────────────
    with tab3:
        sec("Anthropic API 키 설정")
        st.markdown("""
        **Google Gemini API 키 발급 방법**
        1. [aistudio.google.com](https://aistudio.google.com) 접속 (구글 계정으로 로그인)
        2. 좌측 **Get API key** → **Create API key**
        3. 생성된 키(`AIza`로 시작)를 아래에 입력 후 저장
        """)

        cur_key = load_api_key()
        masked  = ("sk-ant-..." + cur_key[-6:]) if len(cur_key) > 10 else ("미설정" if not cur_key else cur_key)
        if cur_key:
            st.markdown(f'<div class="al al-ok">✅&nbsp; API 키 등록됨: <code>{masked}</code></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="al al-warn">⚠️&nbsp; API 키가 없습니다. 아래에 입력해주세요.</div>', unsafe_allow_html=True)

        new_key = st.text_input("API 키 입력", type="password", placeholder="sk-ant-api03-...", key="new_api_key")
        if st.button("저장", type="primary", key="save_api_key_btn"):
            if new_key.startswith("AIza") or new_key.startswith("sk-"):
                save_api_key(new_key)
                st.success("✅ API 키가 저장되었습니다. 페이지를 새로고침하면 AI 기능이 활성화됩니다.")
                st.rerun()
            else:
                st.error("올바른 API 키 형식이 아닙니다. Google API 키는 'AIza'로 시작합니다.")

        if cur_key:
            st.divider()
            if st.button("🗑️ API 키 삭제", key="del_api_key_btn"):
                save_api_key("")
                st.success("삭제되었습니다.")
                st.rerun()

        st.divider()
        sec("AI 기능 현황")
        ai_status = "✅ 활성화" if _api_key else "❌ 비활성화 (API 키 필요)"
        st.markdown(f"""
        | 기능 | 상태 |
        |---|---|
        | 업로드 시 AI 자동분류 (미분류 fallback) | {ai_status} |
        | 저장 시 AI 핵심 키워드 추출 | {ai_status} |
        | 계정과목 검토 AI 일괄분류 버튼 | {ai_status} |
        """)

# ══════════════════════════════════════════════════════════════════════
#  4. 계정 관리 (관리자 전용)
# ══════════════════════════════════════════════════════════════════════
elif page == 'accounts':
    if _auth_user.get("role") != "admin":
        st.error("관리자만 접근할 수 있습니다.")
        st.stop()

    st.markdown('<div class="ph"><div class="ph-title">계정 관리</div><div class="ph-sub">사용자 추가 · 삭제 · 비밀번호 변경</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["사용자 목록", "새 계정 추가", "비밀번호 변경"])

    with tab1:
        sec("전체 사용자")
        users = get_all_users()
        for u in users:
            c1, c2, c3, c4 = st.columns([1.5, 1.5, 1, 1])
            c1.markdown(f"**{u['username']}**")
            c2.markdown(u['name'])
            c3.markdown("🔴 관리자" if u['role'] == 'admin' else "🔵 사용자")
            if u['username'] != 'admin':
                if c4.button("삭제", key=f"del_{u['id']}"):
                    delete_user(u['id'])
                    st.success(f"'{u['username']}' 삭제 완료")
                    st.rerun()
            else:
                c4.markdown("―")
        st.caption(f"총 {len(users)}명")

    with tab2:
        sec("새 계정 추가")
        a1, a2 = st.columns(2)
        new_username = a1.text_input("아이디", key="new_uname")
        new_name     = a2.text_input("이름", key="new_name")
        a3, a4 = st.columns(2)
        new_pw   = a3.text_input("비밀번호", type="password", key="new_upw")
        new_role = a4.selectbox("권한", ["user", "admin"],
                                format_func=lambda x: "관리자" if x == "admin" else "사용자",
                                key="new_urole")
        if st.button("계정 추가", type="primary", key="add_user_btn"):
            if new_username and new_name and new_pw:
                if len(new_pw) < 6:
                    st.error("비밀번호는 6자 이상이어야 합니다.")
                elif add_user(new_username, new_name, new_pw, new_role):
                    st.success(f"✅ '{new_username}' 계정이 추가되었습니다.")
                    st.rerun()
                else:
                    st.error("이미 존재하는 아이디입니다.")
            else:
                st.error("모든 항목을 입력하세요.")

    with tab3:
        sec("비밀번호 변경")
        users = get_all_users()
        unames = [u['username'] for u in users]
        target = st.selectbox("계정 선택", unames, key="chpw_user",
                              format_func=lambda x: next((f"{x} ({u['name']})" for u in users if u['username'] == x), x))
        new_pw1 = st.text_input("새 비밀번호", type="password", key="chpw1")
        new_pw2 = st.text_input("새 비밀번호 확인", type="password", key="chpw2")
        if st.button("변경", type="primary", key="chpw_btn"):
            if not new_pw1 or not new_pw2:
                st.error("비밀번호를 입력하세요.")
            elif new_pw1 != new_pw2:
                st.error("비밀번호가 일치하지 않습니다.")
            elif len(new_pw1) < 6:
                st.error("비밀번호는 6자 이상이어야 합니다.")
            else:
                change_password(target, new_pw1)
                st.success(f"✅ '{target}' 비밀번호가 변경되었습니다.")
