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
from domains.payroll.calculation.service import calc_insured, calc_freelance, calc_business
from domains.payroll.db import get_insurance_actual
from domains.payroll.insurance.service import apply_insurance_actuals, parse_tax_brackets

_now = datetime.now()
EMP_TYPE_LABELS = {
    "insured":    "4대보험",
    "freelance":  "사업소득자",
    "business":   "일반사업자",
    "tax_exempt": "면세사업자",
}


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

        if br_sel == "전체":
            emps = get_all_employees()
        else:
            emps = get_employees_by_branch(br_sel)

        insured_emps   = [e for e in emps if e["emp_type"] == "insured"]
        freelance_emps = [e for e in emps if e["emp_type"] == "freelance"]
        business_emps  = [e for e in emps if e["emp_type"] in ("business", "tax_exempt")]

        if not emps:
            st.info("등록된 직원이 없습니다. 직원 마스터를 먼저 등록하세요.")
            return

        # ── 4대보험 가입자 ──────────────────────────────────
        if insured_emps:
            sec(f"4대보험 가입자 ({len(insured_emps)}명)")
            st.caption("기본급은 직원 마스터에서 자동 불러옵니다. 이번 달 변동이 있으면 수정하세요.")
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

                if st.form_submit_button("4대보험 급여 계산", type="primary", use_container_width=True):
                    ok = 0
                    actual_applied = 0
                    for emp in insured_emps:
                        entry  = calc_insured(emp, year, month, override_gross=overrides[emp["id"]])
                        actual = get_insurance_actual(year, month, emp["id"])
                        if actual:
                            entry = apply_insurance_actuals(entry, actual)
                            actual_applied += 1
                        if save_payroll_entry(entry):
                            ok += 1
                    msg = f"✅ {ok}명 계산 완료"
                    if actual_applied:
                        msg += f" (공단 실납부액 적용 {actual_applied}명)"
                    st.success(msg)
                    st.rerun()

        # ── 사업소득자 ──────────────────────────────────────
        if freelance_emps:
            sec(f"사업소득자 ({len(freelance_emps)}명)")

            # ── 엑셀 일괄 업로드 ────────────────────────────
            with st.expander("📤 엑셀로 일괄 입력 (이름 / 지점 / 세전금액)", expanded=False):
                st.caption(
                    "컬럼: **이름**, **지점**, **세전금액** 3개만 있으면 됩니다. "
                    "이름+지점으로 직원 마스터와 자동 매칭 후 3.3% 원천징수를 계산합니다."
                )
                fl_file = st.file_uploader(
                    "사업소득자_급여.xlsx", type=["xlsx", "xls"],
                    key=f"fl_upload_{year}_{month}",
                )
                if fl_file:
                    try:
                        fl_df = pd.read_excel(fl_file, dtype=str).fillna("")
                        fl_df.columns = [str(c).strip() for c in fl_df.columns]

                        # 컬럼명 유연 매핑
                        name_col   = next((c for c in fl_df.columns if "이름"   in c or "성명" in c or "직원" in c), None)
                        branch_col = next((c for c in fl_df.columns if "지점"   in c or "소속" in c or "부서" in c), None)
                        pay_col    = next((c for c in fl_df.columns if "금액"   in c or "세전" in c or "지급" in c or "급여" in c), None)

                        if not (name_col and branch_col and pay_col):
                            st.error(f"필수 컬럼을 찾지 못했습니다. 현재 컬럼: {list(fl_df.columns)}")
                        else:
                            # 직원 마스터를 (name, branch) 키로 인덱싱
                            emp_map = {(e["name"], e["branch"]): e for e in freelance_emps}

                            preview_rows = []
                            for _, row in fl_df.iterrows():
                                name   = str(row[name_col]).strip()
                                branch = str(row[branch_col]).strip()
                                raw    = str(row[pay_col]).replace(",", "").strip()
                                if not name or name == "nan":
                                    continue
                                try:
                                    gross = int(float(raw)) if raw and raw != "nan" else 0
                                except ValueError:
                                    gross = 0

                                emp    = emp_map.get((name, branch))
                                status = "✅ 매칭" if emp else "⚠️ 직원 없음"
                                tax    = round(gross * 0.033) if emp else 0
                                net    = gross - tax if emp else 0
                                preview_rows.append({
                                    "상태": status,
                                    "이름": name,
                                    "지점": branch,
                                    "세전금액": f"{gross:,}",
                                    "원천징수(3.3%)": f"{tax:,}",
                                    "실수령액": f"{net:,}",
                                    "_emp": emp,
                                    "_gross": gross,
                                })

                            if preview_rows:
                                matched   = [r for r in preview_rows if r["_emp"]]
                                unmatched = [r for r in preview_rows if not r["_emp"]]

                                show_df = pd.DataFrame([
                                    {k: v for k, v in r.items() if not k.startswith("_")}
                                    for r in preview_rows
                                ])
                                st.dataframe(show_df, use_container_width=True, hide_index=True)
                                st.caption(
                                    f"총 {len(preview_rows)}행 — 매칭 {len(matched)}명 / "
                                    f"미매칭 {len(unmatched)}명"
                                    + (f" (미매칭: {', '.join(r['이름']+'('+r['지점']+')' for r in unmatched)})" if unmatched else "")
                                )

                                if matched and st.button(
                                    f"✅ 매칭된 {len(matched)}명 급여 저장 ({year}년 {month}월)",
                                    type="primary", key="fl_bulk_save",
                                ):
                                    ok = 0
                                    for r in matched:
                                        if r["_gross"] > 0:
                                            entry = calc_freelance(r["_emp"], year, month, r["_gross"])
                                            if save_payroll_entry(entry):
                                                ok += 1
                                    st.success(f"✅ {ok}명 저장 완료")
                                    st.rerun()
                    except Exception as ex:
                        st.error(f"파일 읽기 오류: {ex}")

            # ── 개별 직접 입력 폼 ────────────────────────────
            st.caption("이번 달 실지급액을 입력하세요. 3.3% 원천징수 자동 계산.")
            with st.form("freelance_calc_form"):
                payments: dict = {}
                cols_h = st.columns([2, 2, 3, 1])
                for col, hdr in zip(cols_h, ["이름", "지점", "이번달 지급액 (세전)", ""]):
                    col.markdown(f"**{hdr}**")
                for emp in freelance_emps:
                    fi1, fi2, fi3, _ = st.columns([2, 2, 3, 1])
                    fi1.markdown(emp["name"])
                    fi2.markdown(emp["branch"])
                    pay = fi3.number_input("", min_value=0, step=10000, key=f"fl_{emp['id']}",
                                           label_visibility="collapsed")
                    payments[emp["id"]] = pay

                if st.form_submit_button("사업소득자 급여 계산", type="primary", use_container_width=True):
                    ok = 0
                    for emp in freelance_emps:
                        if payments[emp["id"]] > 0:
                            entry = calc_freelance(emp, year, month, payments[emp["id"]])
                            if save_payroll_entry(entry):
                                ok += 1
                    st.success(f"✅ {ok}명 계산 완료")
                    st.rerun()

        # ── 일반/면세사업자 ─────────────────────────────────
        if business_emps:
            sec(f"일반/면세사업자 ({len(business_emps)}개)")
            st.caption("계산서 발행 금액을 입력하세요. 별도 세금 공제 없이 지급 처리됩니다.")
            with st.form("business_calc_form"):
                biz_payments: dict = {}
                cols_h = st.columns([2, 2, 2, 2])
                for col, hdr in zip(cols_h, ["상호명", "지점", "구분", "계산서 금액"]):
                    col.markdown(f"**{hdr}**")
                for emp in business_emps:
                    bi1, bi2, bi3, bi4 = st.columns([2, 2, 2, 2])
                    bi1.markdown(emp["name"])
                    bi2.markdown(emp["branch"])
                    bi3.markdown("일반사업자" if emp["emp_type"] == "business" else "면세사업자")
                    pay = bi4.number_input("", min_value=0, step=10000, key=f"biz_{emp['id']}",
                                           label_visibility="collapsed")
                    biz_payments[emp["id"]] = pay

                if st.form_submit_button("사업자 지급 처리", type="primary", use_container_width=True):
                    ok = 0
                    for emp in business_emps:
                        if biz_payments[emp["id"]] > 0:
                            entry = calc_business(emp, year, month, biz_payments[emp["id"]])
                            if save_payroll_entry(entry):
                                ok += 1
                    st.success(f"✅ {ok}개 처리 완료")
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
                "name": "이름/상호", "branch": "지점", "emp_type": "유형",
                "gross_pay": "지급액(세전)", "meal_allowance": "식대", "transport": "교통비",
                "income_tax": "소득세", "local_tax": "지방세",
                "pension_emp": "국민연금", "health_emp": "건강보험", "employ_emp": "고용보험",
                "total_deduction": "공제합계", "net_pay": "실수령액",
                "company_pension": "연금(회사)", "company_health": "건강(회사)",
                "company_employ": "고용(회사)", "company_accident": "산재",
            }
            show_df = df[[c for c in show_cols if c in df.columns]].copy()
            show_df = show_df.rename(columns=show_cols)
            show_df["유형"] = show_df["유형"].map(EMP_TYPE_LABELS).fillna(show_df["유형"])
            amt_cols = ["지급액(세전)", "식대", "교통비", "소득세", "지방세", "국민연금",
                        "건강보험", "고용보험", "공제합계", "실수령액",
                        "연금(회사)", "건강(회사)", "고용(회사)", "산재"]
            for col in amt_cols:
                if col in show_df.columns:
                    show_df[col] = show_df[col].apply(lambda v: f"{int(v):,}" if pd.notna(v) else "0")

            st.dataframe(show_df, use_container_width=True, hide_index=True, height=500)

            total_net    = sum(e.get("net_pay", 0) for e in entries)
            total_gross  = sum(e.get("gross_pay", 0) for e in entries)
            total_co_ins = sum(
                e.get("company_pension", 0) + e.get("company_health", 0) +
                e.get("company_employ", 0) + e.get("company_accident", 0)
                for e in entries
            )
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("총 지급액 (세전)", f"{total_gross:,}원")
            col_s2.metric("총 실수령 합계", f"{total_net:,}원")
            col_s3.metric("본사 부담 4대보험", f"{total_co_ins:,}원")
            col_s4.metric("인원 수", f"{len(entries)}명")

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
    **국세청 간이세액표 엑셀 업로드** (홈택스 다운로드 원본 그대로 사용)
    - 별도 가공 없이 다운로드한 파일을 그대로 올리면 됩니다.
    - 금액 단위(천원), 헤더 위치, 부양가족 컬럼 자동 처리됩니다.
    """)

    t_col1, t_col2 = st.columns([1, 3])
    tax_year_sel = t_col1.number_input("적용 연도", min_value=2020, max_value=2035,
                                        value=_now.year, step=1, key="tax_year_sel")
    tax_file = t_col2.file_uploader("간이세액표.xlsx (국세청 원본)", type=["xlsx"],
                                     key="tax_bracket_upload")
    if tax_file and st.button("간이세액표 업로드", type="primary", key="tax_bracket_btn"):
        rows, err = parse_tax_brackets(tax_file, int(tax_year_sel))
        if err:
            st.error(f"파싱 오류: {err}")
        elif not rows:
            st.warning("파싱된 데이터가 없습니다.")
        else:
            if upsert_tax_brackets(rows, int(tax_year_sel)):
                st.success(f"✅ {len(rows)}개 구간 저장 완료 (적용연도: {int(tax_year_sel)}년)")
            else:
                st.error("저장 실패")

    brackets = get_tax_brackets(_now.year)
    if brackets:
        st.caption(f"현재 등록된 간이세액표: {_now.year}년 기준 {len(brackets)}개 구간")
    else:
        st.info("간이세액표가 등록되지 않았습니다. 업로드하거나 기본 계산식이 사용됩니다.")
