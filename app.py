import streamlit as st
import pandas as pd
import json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

from modules.db import (
    init_db, load_keyword_rules,
    upsert_card_sales, upsert_bank_transactions, upsert_payroll,
    get_card_by_branch, get_branch_cash_revenue,
    get_expense_by_category, get_payroll_summary,
    get_unreviewed_transactions, update_transaction_classification,
    get_keyword_rules, EXPENSE_CATEGORIES,
)
from modules.parser import (
    parse_card_aggregate, parse_credit_card,
    parse_hana, parse_shinhan,
    parse_payroll_freelance, parse_payroll_insured,
)
from modules.classifier import classify_transactions, add_rule

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
    page_title="라온스포츠 정산",
    layout="wide",
    page_icon="🏋️",
    initial_sidebar_state="auto"
)

# ── 글로벌 CSS ────────────────────────────────────────────
st.markdown("""
<style>
/* 전체 폰트 & 배경 */
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2044 0%, #1a3a6b 100%);
}
[data-testid="stSidebar"] * {
    color: #e8edf5 !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 15px !important;
    padding: 4px 0;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2);
}

/* 상단 타이틀 */
h1 { color: #0f2044; font-weight: 800; letter-spacing: -0.5px; }
h2 { color: #1a3a6b; font-weight: 700; }
h3 { color: #1a3a6b; }

/* 메트릭 카드 커스텀 */
[data-testid="metric-container"] {
    background: #f0f4ff;
    border: 1px solid #d0dcf7;
    border-radius: 12px;
    padding: 16px 20px !important;
    box-shadow: 0 2px 8px rgba(15,32,68,0.08);
}
[data-testid="metric-container"] label {
    color: #5a6a8a !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 22px !important;
    font-weight: 800 !important;
    color: #0f2044 !important;
}

/* 탭 스타일 */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f0f4ff;
    border-radius: 10px;
    padding: 4px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    color: #5a6a8a;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #1a3a6b !important;
    color: white !important;
}

/* 데이터프레임 */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e0e8f0;
}

/* 버튼 */
.stButton > button {
    background: #1a3a6b;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 20px;
}
.stButton > button:hover {
    background: #2554a0;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(26,58,107,0.3);
}

/* 손익 뱃지 */
.profit-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 13px;
}
.profit-pos { background: #e6f4ea; color: #1a7f37; }
.profit-neg { background: #fce8e6; color: #d32f2f; }

/* KPI 강조 카드 */
.kpi-highlight {
    background: linear-gradient(135deg, #1a3a6b 0%, #2554a0 100%);
    color: white;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 8px;
}
.kpi-highlight .label { font-size: 13px; opacity: 0.8; font-weight: 600; }
.kpi-highlight .value { font-size: 26px; font-weight: 900; margin-top: 4px; }
.kpi-green { background: linear-gradient(135deg, #1a7f37 0%, #2ea043 100%); }
.kpi-red   { background: linear-gradient(135deg, #c62828 0%, #e53935 100%); }
.kpi-teal  { background: linear-gradient(135deg, #00695c 0%, #00897b 100%); }

/* 모바일 대응 */
@media (max-width: 768px) {
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 18px !important;
    }
    .kpi-highlight .value { font-size: 20px; }
    h1 { font-size: 22px !important; }
}

/* 구분선 */
.section-divider {
    border: none;
    height: 3px;
    background: linear-gradient(90deg, #1a3a6b, transparent);
    margin: 20px 0;
    border-radius: 2px;
}

/* 알림 배너 */
.alert-box {
    padding: 12px 18px;
    border-radius: 10px;
    margin: 8px 0;
    font-weight: 600;
}
.alert-warning { background: #fff8e1; border-left: 4px solid #f9a825; color: #5d4037; }
.alert-success { background: #e8f5e9; border-left: 4px solid #2e7d32; color: #1b5e20; }
</style>
""", unsafe_allow_html=True)

init_db()
load_keyword_rules()


def fmt(n):
    try:
        v = int(n)
        return f"{v:,}"
    except Exception:
        return "-"


def fmt_won(n):
    try:
        v = int(n)
        if abs(v) >= 100_000_000:
            return f"{v/100_000_000:.1f}억"
        elif abs(v) >= 10_000:
            return f"{v/10_000:.0f}만"
        return f"{v:,}"
    except Exception:
        return "-"


def profit_badge(val):
    try:
        v = int(val)
        if v > 0:
            return f'<span class="profit-badge profit-pos">▲ {v:,}</span>'
        elif v < 0:
            return f'<span class="profit-badge profit-neg">▼ {abs(v):,}</span>'
        else:
            return f'<span class="profit-badge">-</span>'
    except Exception:
        return "-"


# ── 사이드바 ──────────────────────────────────────────────
st.sidebar.markdown("## 🏋️ 라온스포츠")
st.sidebar.markdown("##### 정산 관리 시스템")
st.sidebar.divider()

menu = st.sidebar.radio(
    "메뉴",
    ["🏠 전체 집계", "🏢 지점별 상세", "📤 데이터 업로드", "🔍 미분류 검토", "⚙️ 분류 규칙 관리"],
    label_visibility="collapsed"
)
st.sidebar.divider()
year_sel = st.sidebar.selectbox("📅 연도", [2026, 2025], index=0)
month_sel = st.sidebar.selectbox(
    "📆 월 (지점별 상세)", list(range(1, 13)), index=3,
    format_func=lambda m: f"{m}월"
)
st.sidebar.divider()
st.sidebar.caption("v2.0 · 라온스포츠 정산")


# ── 공통: 지점별 손익 계산 ────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def cached_card(year, month): return get_card_by_branch(year, month)

@st.cache_data(ttl=300, show_spinner=False)
def cached_cash(year, month): return get_branch_cash_revenue(year, month)

@st.cache_data(ttl=300, show_spinner=False)
def cached_pay(year, month): return get_payroll_summary(year, month)

@st.cache_data(ttl=300, show_spinner=False)
def cached_exp(year, month): return get_expense_by_category(year, month)


def build_summary(year: int, month: int | None) -> pd.DataFrame:
    card_df = cached_card(year, month)
    cash_df = cached_cash(year, month)
    pay_df  = cached_pay(year, month)
    exp_df  = cached_exp(year, month)

    card_net    = card_df.set_index("branch")["card_net"]    if not card_df.empty else pd.Series(dtype=float)
    card_supply = card_df.set_index("branch")["card_supply"] if not card_df.empty else pd.Series(dtype=float)
    card_fee    = card_df.set_index("branch")["card_fee"]    if not card_df.empty else pd.Series(dtype=float)
    card_vat    = card_df.set_index("branch")["card_vat"]    if not card_df.empty else pd.Series(dtype=float)

    cash_supply = cash_df.set_index("branch")["cash_supply"] if not cash_df.empty else pd.Series(dtype=float)
    cash_vat    = cash_df.set_index("branch")["cash_vat"]    if not cash_df.empty else pd.Series(dtype=float)

    if not pay_df.empty:
        ins      = pay_df[pay_df["type"] == "insured"].groupby("branch")["net_pay"].sum()
        ins4     = pay_df[pay_df["type"] == "insured"].groupby("branch")["insurance"].sum()
        ins_tax  = pay_df[pay_df["type"] == "insured"].groupby("branch")["income_tax"].sum()
        frl      = pay_df[pay_df["type"] == "freelance"].groupby("branch")["net_pay"].sum()
        frl_tax  = pay_df[pay_df["type"] == "freelance"].groupby("branch")["income_tax"].sum()
        frl_ltax = pay_df[pay_df["type"] == "freelance"].groupby("branch")["local_tax"].sum()
    else:
        ins = ins4 = ins_tax = frl = frl_tax = frl_ltax = pd.Series(dtype=float)

    payroll_cats = {"급여", "4대보험료", "소득세·지방세 합계", "프리랜서", "퇴직금"}
    if not exp_df.empty:
        other = (exp_df[~exp_df["category"].isin(payroll_cats)]
                 .groupby("branch")["amount"].sum())
    else:
        other = pd.Series(dtype=float)

    result = pd.DataFrame({"branch": BRANCH_LIST}).set_index("branch")
    result["카드공급가액"] = card_supply
    result["카드수수료"]   = card_fee
    result["카드VAT"]      = card_vat
    result["카드실수령"]   = card_net
    result["현금공급가액"] = cash_supply
    result["현금VAT"]      = cash_vat
    result["총매출"]       = result["카드실수령"].fillna(0) + result["현금공급가액"].fillna(0)
    result["부가세합계"]   = result["카드VAT"].fillna(0) + result["현금VAT"].fillna(0)
    result["급여"]         = ins
    result["4대보험료"]    = ins4
    result["소득세지방세"] = ins_tax
    result["프리랜서"]     = frl
    result["프리랜서세금"] = frl_tax + frl_ltax
    result["기타지출"]     = other
    result = result.fillna(0)

    result["인건비합계"] = (result["급여"] + result["4대보험료"] + result["소득세지방세"]
                            + result["프리랜서"] + result["프리랜서세금"])
    result["총지출"]     = result["부가세합계"] + result["인건비합계"] + result["기타지출"]
    result["손익"]       = result["총매출"] - result["총지출"]
    result["이익률"]     = result.apply(
        lambda r: round(r["손익"] / r["총매출"] * 100, 1) if r["총매출"] > 0 else 0, axis=1
    )

    return result.reset_index()


def render_kpi_row(result: pd.DataFrame):
    total_rev  = result["총매출"].sum()
    total_exp  = result["총지출"].sum()
    total_prof = result["손익"].sum()
    total_vat  = result["부가세합계"].sum()
    profit_cnt = (result["손익"] > 0).sum()
    total_cnt  = len(result)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="kpi-highlight">
            <div class="label">💰 총 매출</div>
            <div class="value">{fmt_won(total_rev)}원</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-highlight kpi-red">
            <div class="label">💸 총 지출</div>
            <div class="value">{fmt_won(total_exp)}원</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        cls = "kpi-green" if total_prof >= 0 else "kpi-red"
        sign = "▲" if total_prof >= 0 else "▼"
        st.markdown(f"""
        <div class="kpi-highlight {cls}">
            <div class="label">📈 순 손익</div>
            <div class="value">{sign} {fmt_won(abs(total_prof))}원</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-highlight kpi-teal">
            <div class="label">🧾 부가세 합계</div>
            <div class="value">{fmt_won(total_vat)}원</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        ratio = round(profit_cnt / total_cnt * 100) if total_cnt else 0
        cls2 = "kpi-green" if ratio >= 50 else "kpi-red"
        st.markdown(f"""
        <div class="kpi-highlight {cls2}">
            <div class="label">🏆 흑자 지점</div>
            <div class="value">{profit_cnt} / {total_cnt}개</div>
        </div>""", unsafe_allow_html=True)


def render_summary_table(result: pd.DataFrame, view: str = "요약"):
    if view == "요약":
        cols = ["branch", "카드실수령", "현금공급가액", "총매출",
                "부가세합계", "인건비합계", "기타지출", "총지출", "손익", "이익률"]
    else:
        cols = ["branch", "카드공급가액", "카드수수료", "카드VAT", "카드실수령",
                "현금공급가액", "현금VAT", "총매출",
                "급여", "4대보험료", "소득세지방세", "프리랜서", "프리랜서세금",
                "부가세합계", "기타지출", "인건비합계", "총지출", "손익", "이익률"]

    display = result[cols].rename(columns={"branch": "지점"})
    num_cols = [c for c in cols if c not in ("branch",)]
    pct_cols = {"이익률"}
    fmt_dict = {}
    for c in num_cols:
        if c in pct_cols:
            fmt_dict[c] = "{:+.1f}%"
        else:
            fmt_dict[c] = "{:,.0f}"

    def color_row(row):
        styles = [""] * len(row)
        try:
            idx = list(row.index).index("손익")
            val = row["손익"]
            if val > 0:
                styles[idx] = "color: #1a7f37; font-weight: 700"
            elif val < 0:
                styles[idx] = "color: #d32f2f; font-weight: 700"
        except Exception:
            pass
        try:
            idx2 = list(row.index).index("이익률")
            val2 = row["이익률"]
            if val2 > 0:
                styles[idx2] = "color: #1a7f37; font-weight: 600"
            elif val2 < 0:
                styles[idx2] = "color: #d32f2f; font-weight: 600"
        except Exception:
            pass
        return styles

    styled = display.style.apply(color_row, axis=1).format(fmt_dict)
    st.dataframe(styled, use_container_width=True, height=640)


def render_branch_chart(result: pd.DataFrame):
    df_chart = result[result["총매출"] > 0].sort_values("손익", ascending=False)
    if df_chart.empty:
        st.info("표시할 데이터가 없습니다.")
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="총매출",
        x=df_chart["branch"],
        y=df_chart["총매출"],
        marker_color="#1a3a6b",
        text=df_chart["총매출"].apply(fmt_won),
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="총지출",
        x=df_chart["branch"],
        y=df_chart["총지출"],
        marker_color="#e57373",
        opacity=0.85,
    ))
    fig.add_trace(go.Scatter(
        name="손익",
        x=df_chart["branch"],
        y=df_chart["손익"],
        mode="lines+markers",
        line=dict(color="#2ea043", width=3),
        marker=dict(size=8),
        yaxis="y2",
    ))
    fig.update_layout(
        barmode="group",
        yaxis=dict(title="금액(원)", tickformat=","),
        yaxis2=dict(title="손익(원)", overlaying="y", side="right", tickformat=","),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=60),
        font=dict(family="Noto Sans KR"),
        xaxis=dict(tickangle=-30),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_profit_ranking(result: pd.DataFrame):
    df_rank = result[result["총매출"] > 0].sort_values("손익", ascending=True).copy()
    colors = ["#d32f2f" if v < 0 else "#1a7f37" for v in df_rank["손익"]]
    fig = go.Figure(go.Bar(
        x=df_rank["손익"],
        y=df_rank["branch"],
        orientation="h",
        marker_color=colors,
        text=df_rank["손익"].apply(lambda v: f"{v:+,.0f}"),
        textposition="outside",
    ))
    fig.update_layout(
        title="지점별 손익 순위",
        height=max(350, len(df_rank) * 28),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickformat=",", zeroline=True, zerolinecolor="#aaa", zerolinewidth=2),
        margin=dict(t=40, b=20, l=10, r=80),
        font=dict(family="Noto Sans KR"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════
# 1. 전체 집계
# ══════════════════════════════════════════════════════════
if menu == "🏠 전체 집계":
    st.markdown(f"# 📊 전체 집계 &nbsp;—&nbsp; {year_sel}년")
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    tab_labels = [f"{m}월" for m in range(1, 13)] + ["📅 연간 누적"]
    tabs = st.tabs(tab_labels)

    for i, tab in enumerate(tabs):
        with tab:
            month_arg = i + 1 if i < 12 else None
            with st.spinner("데이터 로드 중..."):
                result = build_summary(year_sel, month_arg)

            # KPI 카드
            render_kpi_row(result)
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # 보기 방식
            view = st.radio(
                "보기 방식", ["요약", "상세"],
                key=f"view_{i}", horizontal=True
            )
            render_summary_table(result, view)

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # 차트
            col_chart1, col_chart2 = st.columns([2, 1])
            with col_chart1:
                st.markdown("#### 📊 지점별 매출·지출·손익")
                render_branch_chart(result)
            with col_chart2:
                st.markdown("#### 🏆 손익 순위")
                render_profit_ranking(result)


# ══════════════════════════════════════════════════════════
# 2. 지점별 상세
# ══════════════════════════════════════════════════════════
elif menu == "🏢 지점별 상세":
    st.markdown("# 🏢 지점별 상세")
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    branch_sel = st.selectbox("지점 선택", BRANCH_LIST)

    rows = []
    for m in range(1, 13):
        r = build_summary(year_sel, m)
        row = r[r["branch"] == branch_sel]
        if row.empty:
            rows.append({"월": m, "카드실수령": 0, "카드수수료": 0, "카드VAT": 0,
                         "현금공급가액": 0, "현금VAT": 0, "총매출": 0,
                         "급여": 0, "4대보험료": 0, "소득세지방세": 0,
                         "프리랜서": 0, "프리랜서세금": 0,
                         "부가세합계": 0, "인건비합계": 0, "기타지출": 0,
                         "총지출": 0, "손익": 0, "이익률": 0})
        else:
            d = row.iloc[0].to_dict()
            d["월"] = m
            rows.append(d)

    trend = pd.DataFrame(rows)

    # 연간 KPI
    ann_rev  = trend["총매출"].sum()
    ann_exp  = trend["총지출"].sum()
    ann_prof = trend["손익"].sum()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="kpi-highlight">
            <div class="label">💰 연간 총매출</div>
            <div class="value">{fmt_won(ann_rev)}원</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-highlight kpi-red">
            <div class="label">💸 연간 총지출</div>
            <div class="value">{fmt_won(ann_exp)}원</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        cls = "kpi-green" if ann_prof >= 0 else "kpi-red"
        sign = "▲" if ann_prof >= 0 else "▼"
        st.markdown(f"""
        <div class="kpi-highlight {cls}">
            <div class="label">📈 연간 손익</div>
            <div class="value">{sign} {fmt_won(abs(ann_prof))}원</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # 월별 추이 차트 (Plotly)
    st.markdown(f"#### 📈 {branch_sel} — {year_sel}년 월별 추이")
    month_labels = [f"{m}월" for m in trend["월"]]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name="총매출", x=month_labels, y=trend["총매출"],
        marker_color="#1a3a6b", opacity=0.8,
    ))
    fig2.add_trace(go.Bar(
        name="총지출", x=month_labels, y=trend["총지출"],
        marker_color="#e57373", opacity=0.8,
    ))
    fig2.add_trace(go.Scatter(
        name="손익", x=month_labels, y=trend["손익"],
        mode="lines+markers",
        line=dict(color="#2ea043", width=3),
        marker=dict(size=9,
                    color=["#2ea043" if v >= 0 else "#d32f2f" for v in trend["손익"]],
                    line=dict(width=2, color="white")),
        yaxis="y2",
    ))
    fig2.update_layout(
        barmode="group",
        yaxis=dict(title="금액(원)", tickformat=","),
        yaxis2=dict(title="손익(원)", overlaying="y", side="right", tickformat=","),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=20),
        font=dict(family="Noto Sans KR"),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # 월별 상세 테이블
    st.markdown("#### 📋 월별 계정과목 상세")
    display_trend = trend.copy()
    display_trend["월"] = display_trend["월"].apply(lambda m: f"{m}월")
    display_trend = display_trend.set_index("월")

    detail_cols = ["카드실수령", "카드수수료", "카드VAT",
                   "현금공급가액", "현금VAT", "총매출",
                   "급여", "4대보험료", "소득세지방세",
                   "프리랜서", "프리랜서세금", "부가세합계",
                   "기타지출", "인건비합계", "총지출", "손익", "이익률"]

    def color_trend(row):
        styles = [""] * len(row)
        try:
            idx = list(row.index).index("손익")
            styles[idx] = "color: #1a7f37; font-weight:700" if row["손익"] > 0 else "color: #d32f2f; font-weight:700"
        except Exception:
            pass
        return styles

    fmt_dict2 = {c: ("{:+.1f}%" if c == "이익률" else "{:,.0f}") for c in detail_cols}
    st.dataframe(
        display_trend[detail_cols].style
            .apply(color_trend, axis=1)
            .format(fmt_dict2),
        use_container_width=True,
    )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # 선택 월 지출 파이 차트
    st.markdown(f"#### 🥧 {month_sel}월 지출 구성")
    exp = get_expense_by_category(year_sel, month_sel, branch_sel)
    if not exp.empty:
        exp_g = exp.groupby("category")["amount"].sum().reset_index()
        exp_g = exp_g[exp_g["amount"] > 0].sort_values("amount", ascending=False)

        col_pie, col_bar = st.columns([1, 1])
        with col_pie:
            fig_pie = px.pie(
                exp_g, names="category", values="amount",
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.45,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(
                height=340, showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Noto Sans KR"),
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_bar:
            fig_bar = px.bar(
                exp_g, x="amount", y="category", orientation="h",
                color="amount", color_continuous_scale="Blues",
                text=exp_g["amount"].apply(fmt_won),
            )
            fig_bar.update_traces(textposition="outside")
            fig_bar.update_layout(
                height=340, showlegend=False, coloraxis_showscale=False,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickformat=","),
                margin=dict(t=10, b=10),
                font=dict(family="Noto Sans KR"),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.dataframe(
            exp_g.rename(columns={"category": "계정과목", "amount": "금액"})
                 .style.format({"금액": "{:,.0f}"}),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("해당 월 지출 데이터가 없습니다.")


# ══════════════════════════════════════════════════════════
# 3. 데이터 업로드
# ══════════════════════════════════════════════════════════
elif menu == "📤 데이터 업로드":
    st.markdown("# 📤 데이터 업로드")
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.info("💡 같은 연월 데이터를 다시 올리면 기존 데이터가 교체됩니다. 업로드 전 백업을 권장합니다.")

    tab1, tab2, tab3 = st.tabs(["💳 카드매출", "🏦 통장 내역", "👥 인건비"])

    with tab1:
        st.subheader("카드 매출 업로드")
        col1, col2 = st.columns(2)
        up_year  = col1.number_input("연도", value=2026, min_value=2020, max_value=2030, key="cy")
        up_month = col2.selectbox("월", list(range(1, 13)), index=3, key="cm",
                                  format_func=lambda m: f"{m}월")

        st.markdown("**① 카드사 결과 집계 조회 파일**")
        f1 = st.file_uploader("카드사 결과 집계 조회.xlsx", type=["xlsx"], key="agg")
        if f1 and st.button("📥 카드사 집계 저장", key="btn_agg"):
            with st.spinner("처리 중..."):
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(f1.read())
                    tmp_path = tmp.name
                try:
                    df = parse_card_aggregate(tmp_path, up_year, up_month)
                    upsert_card_sales(df, "card_aggregate", up_year, up_month)
                    unmapped = (df["branch"] == "미매핑").sum()
                    st.success(f"✅ {len(df)}건 저장 완료 (미매핑 {unmapped}건)")
                    if unmapped:
                        st.dataframe(df[df["branch"] == "미매핑"][["raw_merchant", "total_amount"]])
                finally:
                    os.unlink(tmp_path)

        st.markdown("**② 신용카드 파일**")
        f2 = st.file_uploader("신용카드.xlsx", type=["xlsx"], key="cc")
        if f2 and st.button("📥 신용카드 저장", key="btn_cc"):
            with st.spinner("처리 중..."):
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(f2.read())
                    tmp_path = tmp.name
                try:
                    df = parse_credit_card(tmp_path, up_year, up_month)
                    upsert_card_sales(df, "credit_card", up_year, up_month)
                    unmapped = (df["branch"] == "미매핑").sum()
                    st.success(f"✅ {len(df)}건 저장 완료 (미매핑 {unmapped}건)")
                finally:
                    os.unlink(tmp_path)

    with tab2:
        st.subheader("통장 내역 업로드")
        st.caption("카드정산 / 하나 / 신한 탭 포함된 정산내역.xlsx 파일")
        col1, col2 = st.columns(2)
        by = col1.number_input("연도", value=2026, min_value=2020, max_value=2030, key="by")
        bm = col2.selectbox("월", list(range(1, 13)), index=3, key="bm",
                            format_func=lambda m: f"{m}월")
        fb = st.file_uploader("정산내역.xlsx", type=["xlsx"], key="bank")
        if fb and st.button("📥 통장 저장", type="primary", key="btn_bank"):
            with st.spinner("처리 중..."):
                xl = pd.ExcelFile(fb)
                for bank, parser in [("hana", parse_hana), ("shinhan", parse_shinhan)]:
                    try:
                        df = parser(xl, by, bm)
                        df = classify_transactions(df, bank)
                        upsert_bank_transactions(df, bank, by, bm)
                        needs = int(df["needs_review"].sum())
                        label = "하나" if bank == "hana" else "신한"
                        st.success(f"✅ {label}통장: {len(df)}건 저장 (미분류 {needs}건)")
                    except Exception as e:
                        st.error(f"❌ {bank} 오류: {e}")

    with tab3:
        st.subheader("인건비 업로드")
        st.caption("지점별 대시보드.xlsx 파일 (사업소득자 + 4대보험 탭)")
        col1, col2 = st.columns(2)
        py = col1.number_input("연도", value=2026, min_value=2020, max_value=2030, key="py")
        pm = col2.selectbox("월", list(range(1, 13)), index=3, key="pm",
                            format_func=lambda m: f"{m}월")
        fp = st.file_uploader("지점별 대시보드.xlsx", type=["xlsx"], key="payroll")
        if fp and st.button("📥 인건비 저장", type="primary", key="btn_pay"):
            with st.spinner("처리 중..."):
                xl2 = pd.ExcelFile(fp)
                try:
                    df = parse_payroll_freelance(xl2, py, pm)
                    upsert_payroll(df, py, pm, "freelance")
                    st.success(f"✅ 사업소득자(프리랜서): {len(df)}개 지점")
                except Exception as e:
                    st.error(f"❌ 사업소득자 오류: {e}")
                try:
                    df = parse_payroll_insured(xl2, py, pm)
                    upsert_payroll(df, py, pm, "insured")
                    st.success(f"✅ 4대보험 직원: {len(df)}개 지점")
                except Exception as e:
                    st.error(f"❌ 지점별집계 오류: {e}")


# ══════════════════════════════════════════════════════════
# 4. 미분류 검토
# ══════════════════════════════════════════════════════════
elif menu == "🔍 미분류 검토":
    st.markdown("# 🔍 미분류 거래 검토")
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    df = get_unreviewed_transactions()
    if df.empty:
        st.markdown("""
        <div class="alert-box alert-success">
            ✅ 미분류 거래가 없습니다! 모든 거래가 정상 분류되었습니다.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-box alert-warning">
            ⚠️ 미분류 거래 <b>{len(df)}건</b>을 검토해주세요.
        </div>""", unsafe_allow_html=True)

        for _, row in df.iterrows():
            amount = row["deposit"] if row["deposit"] > 0 else row["withdrawal"]
            tp = "입금" if row["deposit"] > 0 else "출금"
            label = f"[{row['bank'].upper()}] {str(row['tx_date'])[:10]}  ·  {row['description']}  ·  {tp} {fmt(amount)}원"
            with st.expander(label):
                c1, c2, c3 = st.columns([2, 2, 1])
                br = c1.selectbox("지점", BRANCH_LIST, key=f"br_{row['id']}")
                ct = c2.selectbox("계정과목", ALL_CATEGORIES, key=f"ct_{row['id']}")
                if c3.button("💾 저장", key=f"sv_{row['id']}"):
                    update_transaction_classification(row["id"], br, ct)
                    add_rule(row["bank"], row["description"], br, ct)
                    st.success("저장 + 규칙 추가 완료!")
                    st.rerun()


# ══════════════════════════════════════════════════════════
# 5. 분류 규칙 관리
# ══════════════════════════════════════════════════════════
elif menu == "⚙️ 분류 규칙 관리":
    st.markdown("# ⚙️ 분류 규칙 관리")
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 규칙 목록", "➕ 규칙 추가"])

    with tab1:
        bank_f = st.selectbox("통장", ["전체", "hana", "shinhan"])
        rules_df = get_keyword_rules(None if bank_f == "전체" else bank_f)
        st.dataframe(rules_df, use_container_width=True)
        st.caption(f"총 {len(rules_df)}개 규칙")

    with tab2:
        st.subheader("새 분류 규칙 추가")
        c1, c2 = st.columns(2)
        nb  = c1.selectbox("통장", ["hana", "shinhan"], key="nb")
        nk  = c2.text_input("키워드 (적요/내용에 포함된 문자)")
        c3, c4 = st.columns(2)
        nbr = c3.selectbox("지점", BRANCH_LIST, key="nbr")
        nct = c4.selectbox("계정과목", ALL_CATEGORIES, key="nct")
        if st.button("➕ 규칙 추가", type="primary"):
            if nk:
                add_rule(nb, nk, nbr, nct)
                st.success(f"✅ 추가 완료: [{nb}] '{nk}' → {nbr} / {nct}")
            else:
                st.error("키워드를 입력하세요.")
