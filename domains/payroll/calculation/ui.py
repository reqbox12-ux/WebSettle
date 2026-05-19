"""
domains/payroll/calculation/ui.py — 급여 계산 UI
"""
from datetime import datetime
import pandas as pd
import streamlit as st

from shared.config import BRANCH_LIST
from shared.utils import fn, sec
from domains.payroll.db import (
    get_all_employees, get_employees_by_branch,
    get_payroll_entries, save_payroll_entry,
    get_insurance_rates, save_insurance_rates,
    get_tax_brackets, upsert_tax_brackets,
    is_payroll_locked, lock_payroll, unlock_payroll,
)
from domains.payroll.calculation.service import calc_insured, calc_freelance

_now = datetime.now()
EMP_TYPE_LABELS = {"insured": "4대보험", "freelance": "사업소득자"}


def render():
    tab_calc, tab_result, tab_settings = st.tabs(["급여 계산", "계산 결과", "⚙️ 요율/세액 설정"])

    # ── 급여 계산 ────────────────────────────────────────────
    with tab_calc:
        col1, col2, col3 = st.columns([1, 1, 2])
        year  = col1.selectbox("연도", list(range(_now.year, _now.year - 3, -1)), key="pay_calc_yr")
        month = col2.selectbox("월", list(range(1, 13)), index=_now.month - 1, key="pay_calc_mn",
                               format_func=lambda m: f"{m}월")
        br_sel = col3.selectbox("지점", ["전체"] + BRANCH_LIST, key="pay_calc_br")

        locked = is_payroll_locked(year, month)
        if locked:
            st.warning(f"⚠️ {year}년 {month}월 급여는 확정(잠금) 상태입니다.")
            if st.session_state.get("auth_user", {}).get("role") == "admin":
                if st.button("🔓 잠금 해제", key="unlock_btn"):
                    unlock_payroll(year, month)
                    st.rerun()
            st.stop()

        # 지점별 직원 목록
        if br_sel == "전체":
            emps = get_all_employees()
        else:
            emps = get_employees_by_branch(br_sel)

        insured_emps   = [e for e in emps if e["emp_type"] == "insured"]
        freelance_emps = [e for e in emps if e["emp_type"] == "freelance"]

        if not emps:
            st.info("등록된 직원이 없습니다. 직원 마스터를 먼저 등록하세요.")
            return

        # ── 4대보험 가입자 ──────────────────────────────────
        if insured_emps:
            sec(f"4대보험 가입자 ({len(insured_emps)}명)")
            st.caption("기본급은 직원 마스터에서 자동 불러옵니다. 이번 달 변동이 있으면 여기서 수정하세요.")
            with st.form("insured_calc_form"):
                overrides: dict = {}
                cols_h = st.columns([2, 2, 2, 2, 1])
                for col, hdr in zip(cols_h, ["이름", "지점", "기본급(자동)", "이번달 기본급", "부양"]):
                    col.markdown(f"**{hdr}**")
                for emp in insured_emps:
                    ci1, ci2, ci3, ci4, ci5 = st.columns([2, 2, 2, 2, 1])
                    ci1.markdown(emp["name"])
                    ci2.markdown(emp["branch"])
                    ci3.markdown(f"{int(emp['base_salary']):,}")
                    ov = ci4.number_input("", min_value=0, value=int(emp["base_salary"]),
                                          step=10000, key=f"ov_{emp['id']}", label_visibility="collapsed")
                    ci5.markdown(str(emp.get("dependents", 1)))
                    overrides[emp["id"]] = ov

                submitted = st.form_submit_button("4대보험 급여 계산", type="primary", use_container_width=True)

            if submitted:
                ok = 0
                for emp in insured_emps:
                    entry = calc_insured(emp, year, month, override_gross=overrides[emp["id"]])
                    if save_payroll_entry(entry):
                        ok += 1
                st.success(f"✅ {ok}명 계산 완료")
                st.rerun()

        # ── 사업소득자 ──────────────────────────────────────
        if freelance_emps:
            sec(f"사업소득자 ({len(freelance_emps)}명)")
            st.caption("이번 달 실지급액을 입력하세요. (3.3% 자동 원천징수)")
            with st.form("freelance_calc_form"):
                payments: dict = {}
                cols_h = st.columns([2, 2, 3, 1])
                for col, hdr in zip(cols_h, ["이름", "지점", "이번달 지급액", ""]):
                    col.markdown(f"**{hdr}**")
                for emp in freelance_emps:
                    fi1, fi2, fi3, _ = st.columns([2, 2, 3, 1])
                    fi1.markdown(emp["name"])
                    fi2.markdown(emp["branch"])
                    pay = fi3.number_input("", min_value=0, step=10000, key=f"fl_{emp['id']}",
                                           label_visibility="collapsed")
                    payments[emp["id"]] = pay

                submitted2 = st.form_submit_button("사업소득자 급여 계산", type="primary", use_container_width=True)

            if submitted2:
                ok = 0
                for emp in freelance_emps:
                    if payments[emp["id"]] > 0:
                        entry = calc_freelance(emp, year, month, payments[emp["id"]])
                        if save_payroll_entry(entry):
                            ok += 1
                st.success(f"✅ {ok}명 계산 완료")
                st.rerun()

        # 급여 확정
        st.divider()
        if st.button("✅ 급여 확정 (잠금)", type="primary", key="lock_payroll_btn"):
            username = st.session_state.get("auth_user", {}).get("username", "unknown")
            lock_payroll(year, month, username)
            st.success(f"🔒 {year}년 {month}월 급여가 확정되었습니다.")
            st.rerun()

    # ── 계산 결과 ────────────────────────────────────────────
    with tab_result:
        col1, col2, col3 = st.columns([1, 1, 2])
        r_year  = col1.selectbox("연도", list(range(_now.year, _now.year - 3, -1)), key="res_yr")
        r_month = col2.selectbox("월", list(range(1, 13)), index=_now.month - 1, key="res_mn",
                                 format_func=lambda m: f"{m}월")
        r_br    = col3.selectbox("지점", ["전체"] + BRANCH_LIST, key="res_br")

        entries = get_payroll_entries(r_year, r_month, None if r_br == "전체" else r_br)
        if not entries:
            st.info("계산된 급여 데이터가 없습니다.")
        else:
            df = pd.DataFrame(entries)
            show_cols = {
                "name": "이름", "branch": "지점", "emp_type": "유형",
                "gross_pay": "기본급", "meal_allowance": "식대", "transport": "교통비",
                "income_tax": "소득세", "local_tax": "지방세",
                "pension_emp": "국민연금", "health_emp": "건강보험", "employ_emp": "고용보험",
                "total_deduction": "공제합계", "net_pay": "실수령액",
                "company_pension": "연금(회사)", "company_health": "건강(회사)",
                "company_employ": "고용(회사)", "company_accident": "산재",
            }
            show_df = df[[c for c in show_cols if c in df.columns]].copy()
            show_df = show_df.rename(columns=show_cols)
            show_df["유형"] = show_df["유형"].map(EMP_TYPE_LABELS).fillna(show_df["유형"])
            for col in ["기본급", "식대", "교통비", "소득세", "지방세", "국민연금",
                        "건강보험", "고용보험", "공제합계", "실수령액",
                        "연금(회사)", "건강(회사)", "고용(회사)", "산재"]:
                if col in show_df.columns:
                    show_df[col] = show_df[col].apply(lambda v: f"{int(v):,}" if pd.notna(v) else "0")

            st.dataframe(show_df, use_container_width=True, hide_index=True, height=500)

            # 합계
            total_net    = sum(e.get("net_pay", 0) for e in entries)
            total_co_ins = sum(
                e.get("company_pension", 0) + e.get("company_health", 0) +
                e.get("company_employ", 0) + e.get("company_accident", 0)
                for e in entries
            )
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("총 실수령 합계", f"{total_net:,}원")
            col_s2.metric("본사 부담 4대보험", f"{total_co_ins:,}원")
            col_s3.metric("인원 수", f"{len(entries)}명")

    # ── 요율/세액 설정 ────────────────────────────────────────
    with tab_settings:
        _render_settings()


def _render_settings():
    sec("4대보험 요율 설정")
    rates = get_insurance_rates(_now.year)

    with st.form("insurance_rates_form"):
        col1, col2 = st.columns(2)
        r_year = col1.number_input("적용 연도", min_value=2020, max_value=2035,
                                    value=rates["year"], step=1, key="rates_year")
        col2.markdown(" ")

        col3, col4, col5 = st.columns(3)
        pension = col3.number_input("국민연금 (직원)", min_value=0.0, max_value=0.1,
                                     value=float(rates["pension_rate"]), format="%.4f", key="r_pension")
        health  = col4.number_input("건강보험 (직원)", min_value=0.0, max_value=0.1,
                                     value=float(rates["health_rate"]), format="%.5f", key="r_health")
        employ_emp = col5.number_input("고용보험 (직원)", min_value=0.0, max_value=0.05,
                                        value=float(rates["employ_rate_emp"]), format="%.4f", key="r_employ_emp")

        col6, col7 = st.columns(2)
        employ_co  = col6.number_input("고용보험 (회사)", min_value=0.0, max_value=0.05,
                                        value=float(rates["employ_rate_co"]), format="%.4f", key="r_employ_co")
        accident   = col7.number_input("산재보험 (회사, 업종별)", min_value=0.0, max_value=0.1,
                                        value=float(rates["accident_rate"]), format="%.4f", key="r_accident")

        if st.form_submit_button("요율 저장", type="primary"):
            ok = save_insurance_rates({
                "year": int(r_year), "pension_rate": pension, "health_rate": health,
                "employ_rate_emp": employ_emp, "employ_rate_co": employ_co, "accident_rate": accident,
            })
            st.success("✅ 저장 완료") if ok else st.error("저장 실패")

    st.divider()
    sec("간이세액표 업로드")
    st.markdown("""
    **국세청 간이세액표 엑셀 업로드**
    - 국세청 홈택스에서 다운로드한 간이세액표 파일을 업로드하세요.
    - 컬럼: `salary_from`, `salary_to`, `dependents_0` ~ `dependents_7`, `tax_year`
    """)

    tax_file = st.file_uploader("간이세액표.xlsx", type=["xlsx"], key="tax_bracket_upload")
    if tax_file and st.button("간이세액표 업로드", type="primary", key="tax_bracket_btn"):
        try:
            import pandas as pd
            df  = pd.read_excel(tax_file).fillna(0)
            rows = df.to_dict("records")
            tax_yr = int(rows[0].get("tax_year", _now.year)) if rows else _now.year
            if upsert_tax_brackets(rows, tax_yr):
                st.success(f"✅ {len(rows)}개 구간 저장 완료 (적용연도: {tax_yr})")
            else:
                st.error("저장 실패")
        except Exception as e:
            st.error(f"오류: {e}")

    # 현재 적용 세액표 확인
    brackets = get_tax_brackets(_now.year)
    if brackets:
        st.caption(f"현재 등록된 간이세액표: {_now.year}년 기준 {len(brackets)}개 구간")
    else:
        st.info("간이세액표가 등록되지 않았습니다. 업로드하거나 기본 계산식이 사용됩니다.")
