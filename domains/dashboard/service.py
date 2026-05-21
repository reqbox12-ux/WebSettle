"""
domains/dashboard/service.py — 대시보드 데이터 집계 서비스
"""
import pandas as pd
import streamlit as st
from shared.db import (
    get_card_by_branch, get_branch_cash_revenue, get_payroll_summary,
    get_expense_by_category, get_revenue_by_category, get_insurance_summary,
)
from shared.config import BRANCH_LIST
from domains.branch.db import get_branch_monthly_revenue

# 월별 수동입력 매출 컬럼 (카페인건비 제외)
_BMR_REVENUE_COLS = ["dogeub", "pt_sales", "gx_sales", "cafe_sales",
                     "golf_sales", "facility_fee", "other_sales"]


# ── 캐시 래퍼 ───────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def c_card(y, m):
    return get_card_by_branch(y, m)


@st.cache_data(ttl=300, show_spinner=False)
def c_cash(y, m):
    return get_branch_cash_revenue(y, m)


@st.cache_data(ttl=300, show_spinner=False)
def c_pay(y, m):
    return get_payroll_summary(y, m)


@st.cache_data(ttl=300, show_spinner=False)
def c_exp(y, m):
    return get_expense_by_category(y, m)


@st.cache_data(ttl=300, show_spinner=False)
def c_rev(y, m):
    return get_revenue_by_category(y, m)


@st.cache_data(ttl=300, show_spinner=False)
def c_ins(y, m):
    return get_insurance_summary(y, m)


@st.cache_data(ttl=300, show_spinner=False)
def c_bmr(y, m):
    """월별 수동입력 매출 (branch_monthly_revenue)"""
    rows = get_branch_monthly_revenue(y, m)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def build_summary(year: int, month: int) -> pd.DataFrame:
    """모든 지점의 월별 매출/지출/손익 집계"""
    card_df = c_card(year, month)
    cash_df = c_cash(year, month)
    pay_df  = c_pay(year, month)
    exp_df  = c_exp(year, month)
    ins_df  = c_ins(year, month)
    bmr_df  = c_bmr(year, month)

    def s(df, col):
        return df.set_index("branch")[col] if not df.empty else pd.Series(dtype=float)

    card_sup = s(card_df, "card_supply")
    card_fee = s(card_df, "card_fee")
    card_vat = s(card_df, "card_vat")
    card_net = s(card_df, "card_net")
    cash_sup = s(cash_df, "cash_supply")
    cash_vat = s(cash_df, "cash_vat")

    if not pay_df.empty:
        ins   = pay_df[pay_df.type == "insured"].groupby("branch")["net_pay"].sum()
        ins4  = pay_df[pay_df.type == "insured"].groupby("branch")["insurance"].sum()
        ins_t = pay_df[pay_df.type == "insured"].groupby("branch")["income_tax"].sum()
        frl   = pay_df[pay_df.type == "freelance"].groupby("branch")["net_pay"].sum()
        frl_t = pay_df[pay_df.type == "freelance"].groupby("branch")["income_tax"].sum()
        frl_l = pay_df[pay_df.type == "freelance"].groupby("branch")["local_tax"].sum()
    else:
        ins = ins4 = ins_t = frl = frl_t = frl_l = pd.Series(dtype=float)

    ins_co  = s(ins_df, "company_insurance")  if not ins_df.empty else pd.Series(dtype=float)
    ins_emp = s(ins_df, "employee_insurance") if not ins_df.empty else pd.Series(dtype=float)

    pc = {"급여", "4대보험료", "소득세·지방세 합계", "프리랜서", "퇴직금"}
    other = (
        exp_df[~exp_df.category.isin(pc)].groupby("branch")["amount"].sum()
        if not exp_df.empty
        else pd.Series(dtype=float)
    )

    # ── 월별 수동입력 매출 집계 ─────────────────────────────
    if not bmr_df.empty and "branch" in bmr_df.columns:
        bmr_idx = bmr_df.set_index("branch")
        bmr_rev = sum(
            bmr_idx[c].fillna(0) if c in bmr_idx.columns else pd.Series(dtype=float)
            for c in _BMR_REVENUE_COLS
        )
        bmr_labor = (
            bmr_idx["cafe_labor"].fillna(0)
            if "cafe_labor" in bmr_idx.columns
            else pd.Series(dtype=float)
        )
    else:
        bmr_rev   = pd.Series(dtype=float)
        bmr_labor = pd.Series(dtype=float)

    r = pd.DataFrame({"branch": BRANCH_LIST}).set_index("branch")
    r["카드공급가액"] = card_sup
    r["카드VAT"]     = card_vat
    r["카드수수료"]   = card_fee
    r["카드실수령"]   = card_net
    r["현금VAT"]     = cash_vat
    r["현금공급가액"] = cash_sup
    r["수동입력매출"] = bmr_rev     # 월별 직접입력 매출 합계
    r["카페인건비"]   = bmr_labor   # 카페인건비 (비용)
    r["총매출"]       = (r["카드실수령"].fillna(0)
                        + r["현금공급가액"].fillna(0)
                        + r["수동입력매출"].fillna(0))
    r["부가세합계"]   = r["카드VAT"].fillna(0) + r["현금VAT"].fillna(0)
    r["급여"]         = ins
    r["4대보험료_직원"] = ins4
    r["소득세지방세"]  = ins_t
    r["4대보험_본사"]  = ins_co
    r["4대보험_직원"]  = ins_emp
    r["프리랜서"]     = frl
    r["프리랜서세금"]  = frl_t + frl_l
    r["기타지출"]     = other
    r = r.fillna(0)
    r["인건비합계"] = (
        r["급여"] + r["4대보험료_직원"] + r["소득세지방세"]
        + r["프리랜서"] + r["프리랜서세금"] + r["4대보험_본사"]
        + r["카페인건비"]
    )
    r["총지출"]  = r["부가세합계"] + r["인건비합계"] + r["기타지출"]
    r["손익"]    = r["총매출"] - r["총지출"]
    r["이익률"]  = r.apply(
        lambda x: round(x["손익"] / x["총매출"] * 100, 1) if x["총매출"] > 0 else 0,
        axis=1,
    )
    return r.reset_index()
