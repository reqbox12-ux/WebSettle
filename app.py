import streamlit as st
import pandas as pd
import json
from pathlib import Path

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

st.set_page_config(page_title="라온스포츠 정산 대시보드", layout="wide", page_icon="📊")

init_db()
load_keyword_rules()


def fmt(n):
    try:
        v = int(n)
        return f"{v:,}"
    except Exception:
        return "-"


def fmt_delta(n):
    v = int(n) if n else 0
    sign = "+" if v > 0 else ""
    return f"{sign}{v:,}"


# ── 사이드바 ──────────────────────────────────────────────
st.sidebar.title("📊 라온스포츠 정산")
menu = st.sidebar.radio(
    "메뉴",
    ["🏠 전체 집계", "🏢 지점별 상세", "📤 데이터 업로드", "🔍 미분류 검토", "⚙️ 분류 규칙 관리"]
)
st.sidebar.divider()
year_sel = st.sidebar.selectbox("연도", [2026, 2025], index=0)
month_sel = st.sidebar.selectbox(
    "월 (지점별 상세 기준)", list(range(1, 13)), index=3,
    format_func=lambda m: f"{m}월"
)


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
    card_df   = cached_card(year, month)
    cash_df   = cached_cash(year, month)
    pay_df    = cached_pay(year, month)
    exp_df    = cached_exp(year, month)

    # 카드 수입
    card_net    = card_df.set_index("branch")["card_net"]    if not card_df.empty else pd.Series(dtype=float)
    card_supply = card_df.set_index("branch")["card_supply"] if not card_df.empty else pd.Series(dtype=float)
    card_fee    = card_df.set_index("branch")["card_fee"]    if not card_df.empty else pd.Series(dtype=float)
    card_vat    = card_df.set_index("branch")["card_vat"]    if not card_df.empty else pd.Series(dtype=float)

    # 현금 수입 (공급가액 = deposit - vat)
    cash_supply = cash_df.set_index("branch")["cash_supply"] if not cash_df.empty else pd.Series(dtype=float)
    cash_vat    = cash_df.set_index("branch")["cash_vat"]    if not cash_df.empty else pd.Series(dtype=float)

    # 인건비
    if not pay_df.empty:
        ins      = pay_df[pay_df["type"] == "insured"].groupby("branch")["net_pay"].sum()
        ins4     = pay_df[pay_df["type"] == "insured"].groupby("branch")["insurance"].sum()
        ins_tax  = pay_df[pay_df["type"] == "insured"].groupby("branch")["income_tax"].sum()
        frl      = pay_df[pay_df["type"] == "freelance"].groupby("branch")["net_pay"].sum()   # 실지급액
        frl_tax  = pay_df[pay_df["type"] == "freelance"].groupby("branch")["income_tax"].sum()
        frl_ltax = pay_df[pay_df["type"] == "freelance"].groupby("branch")["local_tax"].sum()
    else:
        ins = ins4 = ins_tax = frl = frl_tax = frl_ltax = pd.Series(dtype=float)

    # 기타 지출 (통장 기준, 인건비성 제외)
    payroll_cats = {"급여", "4대보험료", "소득세·지방세 합계", "프리랜서", "퇴직금"}
    if not exp_df.empty:
        other = (exp_df[~exp_df["category"].isin(payroll_cats)]
                 .groupby("branch")["amount"].sum())
    else:
        other = pd.Series(dtype=float)

    result = pd.DataFrame({"branch": BRANCH_LIST}).set_index("branch")
    result["카드공급가액"] = card_supply   # 카드 총액 - VAT
    result["카드수수료"]   = card_fee
    result["카드VAT"]      = card_vat
    result["카드실수령"]   = card_net      # 공급가액 - 수수료
    result["현금공급가액"] = cash_supply   # 현금 총액 - VAT
    result["현금VAT"]      = cash_vat
    result["총매출"]       = result["카드실수령"].fillna(0) + result["현금공급가액"].fillna(0)
    result["부가세합계"]   = result["카드VAT"].fillna(0) + result["현금VAT"].fillna(0)
    result["급여"]       = ins
    result["4대보험료"]  = ins4
    result["소득세지방세"] = ins_tax
    result["프리랜서"]   = frl
    result["프리랜서세금"] = frl_tax + frl_ltax
    result["기타지출"]   = other
    result = result.fillna(0)

    result["인건비합계"] = (result["급여"] + result["4대보험료"] + result["소득세지방세"]
                            + result["프리랜서"] + result["프리랜서세금"])
    result["총지출"]     = (result["부가세합계"] + result["인건비합계"] + result["기타지출"])
    result["손익"]       = result["총매출"] - result["총지출"]

    return result.reset_index()


def render_summary_table(result: pd.DataFrame):
    def color_profit(val):
        if isinstance(val, (int, float)):
            return "color: blue; font-weight:bold" if val > 0 else ("color: red; font-weight:bold" if val < 0 else "")
        return ""

    num_cols = ["카드공급가액", "카드수수료", "카드VAT", "카드실수령",
                "현금공급가액", "현금VAT", "총매출", "부가세합계",
                "인건비합계", "기타지출", "총지출", "손익"]
    display = result[["branch"] + num_cols].rename(columns={"branch": "지점"})
    st.dataframe(
        display.style
            .map(color_profit, subset=["손익"])
            .format({c: "{:,.0f}" for c in num_cols}),
        use_container_width=True, height=620,
    )


# ══════════════════════════════════════════════════════════
# 1. 전체 집계
# ══════════════════════════════════════════════════════════
if menu == "🏠 전체 집계":
    st.title(f"📊 전체 집계 — {year_sel}년")

    tab_labels = [f"{m}월" for m in range(1, 13)] + ["📅 연간 누적"]
    tabs = st.tabs(tab_labels)

    for i, tab in enumerate(tabs):
        with tab:
            result = build_summary(year_sel, i + 1 if i < 12 else None)

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("총 매출",    f"{result['총매출'].sum():,.0f}원")
            c2.metric("총 지출",    f"{result['총지출'].sum():,.0f}원")
            c3.metric("손 익",      f"{result['손익'].sum():,.0f}원")
            c4.metric("부가세 합계", f"{result['부가세합계'].sum():,.0f}원")
            c5.metric("흑자 지점",  f"{(result['손익'] > 0).sum()}개 / {len(result)}개")

            st.divider()

            view = st.radio(
                "보기 방식", ["요약", "상세"],
                key=f"view_{i}", horizontal=True
            )
            if view == "요약":
                render_summary_table(result)
            else:
                detail_cols = ["branch", "카드공급가액", "카드수수료", "카드VAT", "카드실수령",
                               "현금공급가액", "현금VAT", "총매출",
                               "급여", "4대보험료", "소득세지방세",
                               "프리랜서", "프리랜서세금", "기타지출", "총지출", "손익"]
                display = result[detail_cols].rename(columns={"branch": "지점"})
                num_cols = detail_cols[1:]
                st.dataframe(
                    display.style.format({c: "{:,.0f}" for c in num_cols}),
                    use_container_width=True, height=620,
                )

            st.subheader("손익 순 차트")
            chart = result.set_index("branch")[["총매출", "총지출"]].sort_values("총매출", ascending=False)
            st.bar_chart(chart)


# ══════════════════════════════════════════════════════════
# 2. 지점별 상세
# ══════════════════════════════════════════════════════════
elif menu == "🏢 지점별 상세":
    st.title("🏢 지점별 상세")

    branch_sel = st.selectbox("지점 선택", BRANCH_LIST)

    # 연간 월별 추이
    rows = []
    for m in range(1, 13):
        r = build_summary(year_sel, m)
        row = r[r["branch"] == branch_sel]
        if row.empty:
            rows.append({"월": f"{m}월",
                         "카드실수령": 0, "카드수수료": 0, "카드VAT": 0,
                         "현금공급가액": 0, "현금VAT": 0,
                         "총매출": 0, "부가세합계": 0,
                         "인건비합계": 0, "기타지출": 0,
                         "총지출": 0, "손익": 0})
        else:
            d = row.iloc[0].to_dict()
            d["월"] = f"{m}월"
            rows.append(d)

    trend = pd.DataFrame(rows).set_index("월")
    num_cols = ["카드실수령", "카드수수료", "카드VAT",
                "현금공급가액", "현금VAT",
                "총매출", "부가세합계",
                "인건비합계", "기타지출", "총지출", "손익"]

    c1, c2, c3 = st.columns(3)
    c1.metric("연간 총매출", f"{trend['총매출'].sum():,.0f}원")
    c2.metric("연간 총지출", f"{trend['총지출'].sum():,.0f}원")
    c3.metric("연간 손익",   f"{trend['손익'].sum():,.0f}원")

    st.divider()
    st.subheader(f"{branch_sel} — {year_sel}년 월별 추이")
    st.line_chart(trend[["총매출", "총지출", "손익"]])

    st.subheader("월별 상세")
    st.dataframe(
        trend[num_cols].style.format("{:,.0f}"),
        use_container_width=True,
    )

    # 선택 월 계정과목별 지출
    st.subheader(f"{month_sel}월 계정과목별 지출")
    exp = get_expense_by_category(year_sel, month_sel, branch_sel)
    if not exp.empty:
        exp_g = exp.groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False)
        st.bar_chart(exp_g.set_index("category")["amount"])
        st.dataframe(
            exp_g.rename(columns={"category": "계정과목", "amount": "금액"})
                 .style.format({"금액": "{:,.0f}"}),
            use_container_width=True,
        )
    else:
        st.info("해당 월 지출 데이터가 없습니다.")


# ══════════════════════════════════════════════════════════
# 3. 데이터 업로드
# ══════════════════════════════════════════════════════════
elif menu == "📤 데이터 업로드":
    st.title("📤 데이터 업로드")

    tab1, tab2, tab3 = st.tabs(["카드매출 (카드사 파일)", "통장 내역", "인건비"])

    # ── 카드매출
    with tab1:
        st.subheader("카드 매출 업로드")
        col1, col2 = st.columns(2)
        up_year  = col1.number_input("연도", value=2026, min_value=2020, max_value=2030, key="cy")
        up_month = col2.selectbox("월", list(range(1, 13)), index=3, key="cm",
                                  format_func=lambda m: f"{m}월")

        st.markdown("**① 카드사 결과 집계 조회 파일**")
        f1 = st.file_uploader("카드사 결과 집계 조회.xlsx", type=["xlsx"], key="agg")
        if f1 and st.button("카드사 집계 저장", key="btn_agg"):
            with st.spinner("처리 중..."):
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(f1.read())
                    tmp_path = tmp.name
                try:
                    df = parse_card_aggregate(tmp_path, up_year, up_month)
                    upsert_card_sales(df, "card_aggregate", up_year, up_month)
                    unmapped = (df["branch"] == "미매핑").sum()
                    st.success(f"{len(df)}건 저장 완료 (미매핑 {unmapped}건)")
                    if unmapped:
                        st.dataframe(df[df["branch"] == "미매핑"][["raw_merchant", "total_amount"]])
                finally:
                    os.unlink(tmp_path)

        st.markdown("**② 신용카드 파일**")
        f2 = st.file_uploader("신용카드.xlsx", type=["xlsx"], key="cc")
        if f2 and st.button("신용카드 저장", key="btn_cc"):
            with st.spinner("처리 중..."):
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(f2.read())
                    tmp_path = tmp.name
                try:
                    df = parse_credit_card(tmp_path, up_year, up_month)
                    upsert_card_sales(df, "credit_card", up_year, up_month)
                    unmapped = (df["branch"] == "미매핑").sum()
                    st.success(f"{len(df)}건 저장 완료 (미매핑 {unmapped}건)")
                finally:
                    os.unlink(tmp_path)

    # ── 통장
    with tab2:
        st.subheader("통장 내역 업로드 (정산내역.xlsx)")
        st.caption("카드정산 / 하나 / 신한 탭 포함 파일")
        col1, col2 = st.columns(2)
        by = col1.number_input("연도", value=2026, min_value=2020, max_value=2030, key="by")
        bm = col2.selectbox("월", list(range(1, 13)), index=3, key="bm",
                            format_func=lambda m: f"{m}월")
        fb = st.file_uploader("정산내역.xlsx", type=["xlsx"], key="bank")
        if fb and st.button("통장 저장", type="primary", key="btn_bank"):
            with st.spinner("처리 중..."):
                xl = pd.ExcelFile(fb)
                for bank, parser in [("hana", parse_hana), ("shinhan", parse_shinhan)]:
                    try:
                        df = parser(xl, by, bm)
                        df = classify_transactions(df, bank)
                        upsert_bank_transactions(df, bank, by, bm)
                        needs = int(df["needs_review"].sum())
                        label = "하나" if bank == "hana" else "신한"
                        st.success(f"{label}통장: {len(df)}건 저장 (미분류 {needs}건)")
                    except Exception as e:
                        st.error(f"{bank} 오류: {e}")

    # ── 인건비
    with tab3:
        st.subheader("인건비 업로드 (지점별 대시보드.xlsx)")
        col1, col2 = st.columns(2)
        py = col1.number_input("연도", value=2026, min_value=2020, max_value=2030, key="py")
        pm = col2.selectbox("월", list(range(1, 13)), index=3, key="pm",
                            format_func=lambda m: f"{m}월")
        fp = st.file_uploader("지점별 대시보드.xlsx", type=["xlsx"], key="payroll")
        if fp and st.button("인건비 저장", type="primary", key="btn_pay"):
            with st.spinner("처리 중..."):
                xl2 = pd.ExcelFile(fp)
                try:
                    df = parse_payroll_freelance(xl2, py, pm)
                    upsert_payroll(df, py, pm, "freelance")
                    st.success(f"사업소득자(프리랜서): {len(df)}개 지점")
                except Exception as e:
                    st.error(f"사업소득자 오류: {e}")
                try:
                    df = parse_payroll_insured(xl2, py, pm)
                    upsert_payroll(df, py, pm, "insured")
                    st.success(f"4대보험 직원: {len(df)}개 지점")
                except Exception as e:
                    st.error(f"지점별집계 오류: {e}")


# ══════════════════════════════════════════════════════════
# 4. 미분류 검토
# ══════════════════════════════════════════════════════════
elif menu == "🔍 미분류 검토":
    st.title("🔍 미분류 거래 검토")

    df = get_unreviewed_transactions()
    if df.empty:
        st.success("미분류 거래가 없습니다! ✅")
    else:
        st.warning(f"미분류 거래 **{len(df)}건**을 검토해주세요.")
        for _, row in df.iterrows():
            amount = row["deposit"] if row["deposit"] > 0 else row["withdrawal"]
            label = f"[{row['bank'].upper()}] {str(row['tx_date'])[:10]}  |  {row['description']}  |  {fmt(amount)}원"
            with st.expander(label):
                c1, c2, c3 = st.columns([2, 2, 1])
                br = c1.selectbox("지점", BRANCH_LIST, key=f"br_{row['id']}")
                ct = c2.selectbox("계정과목", ALL_CATEGORIES, key=f"ct_{row['id']}")
                if c3.button("저장", key=f"sv_{row['id']}"):
                    update_transaction_classification(row["id"], br, ct)
                    add_rule(row["bank"], row["description"], br, ct)
                    st.success("저장 + 규칙 추가 완료")
                    st.rerun()


# ══════════════════════════════════════════════════════════
# 5. 분류 규칙 관리
# ══════════════════════════════════════════════════════════
elif menu == "⚙️ 분류 규칙 관리":
    st.title("⚙️ 분류 규칙 관리")

    tab1, tab2 = st.tabs(["규칙 목록", "규칙 추가"])

    with tab1:
        bank_f = st.selectbox("통장", ["전체", "hana", "shinhan"])
        rules_df = get_keyword_rules(None if bank_f == "전체" else bank_f)
        st.dataframe(rules_df, use_container_width=True)

    with tab2:
        st.subheader("새 분류 규칙 추가")
        c1, c2 = st.columns(2)
        nb = c1.selectbox("통장", ["hana", "shinhan"], key="nb")
        nk = c2.text_input("키워드 (적요/내용에 포함된 문자)")
        c3, c4 = st.columns(2)
        nbr = c3.selectbox("지점", BRANCH_LIST, key="nbr")
        nct = c4.selectbox("계정과목", ALL_CATEGORIES, key="nct")
        if st.button("추가", type="primary"):
            if nk:
                add_rule(nb, nk, nbr, nct)
                st.success(f"추가 완료: [{nb}] '{nk}' → {nbr} / {nct}")
            else:
                st.error("키워드를 입력하세요.")
