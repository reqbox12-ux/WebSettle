"""
domains/payroll/employee/ui.py — 직원 마스터 관리 UI
"""
import streamlit as st
import pandas as pd

from shared.config import BRANCH_LIST
from shared.utils import sec
from domains.payroll.db import (
    get_all_employees, get_employees_by_branch,
    upsert_employee, delete_employee,
)
from domains.payroll.employee.service import import_employees_from_excel

EMP_TYPE_LABELS = {"insured": "4대보험", "freelance": "사업소득자"}


def render():
    sec("직원 마스터")

    tab_list, tab_add, tab_import = st.tabs(["직원 목록", "직원 추가/수정", "엑셀 일괄 등록"])

    # ── 직원 목록 ────────────────────────────────────────────
    with tab_list:
        col_f1, col_f2 = st.columns([2, 1])
        sel_br   = col_f1.selectbox("지점 필터", ["전체"] + BRANCH_LIST, key="emp_br_filter")
        show_all = col_f2.checkbox("퇴직자 포함", value=False, key="emp_show_all")

        if sel_br == "전체":
            emps = get_all_employees(active_only=not show_all)
        else:
            emps = get_employees_by_branch(sel_br, active_only=not show_all)

        if not emps:
            st.info("등록된 직원이 없습니다.")
        else:
            df = pd.DataFrame(emps)
            display_cols = {
                "id": "ID", "name": "이름", "branch": "지점",
                "emp_type": "유형", "dependents": "부양가족",
                "base_salary": "기본급", "meal_allowance": "식대",
                "transport": "교통비", "email": "이메일",
                "join_date": "입사/등록일", "is_active": "재직",
            }
            show_df = df[[c for c in display_cols if c in df.columns]].copy()
            show_df = show_df.rename(columns=display_cols)
            show_df["유형"] = show_df["유형"].map(EMP_TYPE_LABELS).fillna(show_df["유형"])
            show_df["재직"] = show_df["재직"].apply(lambda v: "✅" if v else "❌")
            for col in ["기본급", "식대", "교통비"]:
                if col in show_df.columns:
                    show_df[col] = show_df[col].apply(lambda v: f"{int(v):,}" if pd.notna(v) else "0")

            st.dataframe(show_df, use_container_width=True, hide_index=True, height=450)
            st.caption(f"총 {len(emps)}명")

            # 삭제 (비활성화)
            st.divider()
            del_id = st.number_input("삭제할 직원 ID", min_value=1, step=1, key="del_emp_id")
            if st.button("직원 비활성화 (퇴직처리)", key="del_emp_btn"):
                if delete_employee(int(del_id)):
                    st.success("처리 완료")
                    st.rerun()
                else:
                    st.error("처리 실패")

    # ── 직원 추가/수정 ────────────────────────────────────────
    with tab_add:
        st.markdown("##### 직원 정보 입력")
        col1, col2, col3 = st.columns(3)
        emp_id   = col1.number_input("ID (수정 시 입력, 신규는 0)", min_value=0, step=1, key="emp_edit_id")
        emp_name = col2.text_input("이름 *", key="emp_name")
        emp_br   = col3.selectbox("소속지점 *", BRANCH_LIST, key="emp_branch")

        col4, col5, col6 = st.columns(3)
        emp_type = col4.selectbox("유형 *", ["insured", "freelance"],
                                  format_func=lambda x: EMP_TYPE_LABELS[x], key="emp_type")
        emp_dep  = col5.number_input("부양가족수 (본인 포함)", min_value=0, max_value=10, value=1, key="emp_dep")
        emp_join = col6.text_input("입사/등록일 (YYYY-MM-DD)", key="emp_join")

        col7, col8, col9 = st.columns(3)
        emp_base  = col7.number_input("세전기본급", min_value=0, step=10000, key="emp_base",
                                       help="사업소득자는 0 입력")
        emp_meal  = col8.number_input("식대", min_value=0, step=10000, value=100000, key="emp_meal")
        emp_trans = col9.number_input("교통비", min_value=0, step=10000, key="emp_trans")

        col10, col11 = st.columns(2)
        emp_email  = col10.text_input("이메일", key="emp_email")
        emp_idnum  = col11.text_input("주민등록번호 (사업소득자)", type="password", key="emp_idnum",
                                       help="원천징수영수증 발급용. 암호화 저장됩니다.")
        emp_note   = st.text_input("비고", key="emp_note")

        if st.button("저장", type="primary", key="emp_save_btn"):
            if not emp_name or not emp_br:
                st.error("이름과 지점은 필수입니다.")
            else:
                data = {
                    "id":           int(emp_id) if emp_id else None,
                    "name":         emp_name.strip(),
                    "branch":       emp_br,
                    "emp_type":     emp_type,
                    "dependents":   int(emp_dep),
                    "base_salary":  int(emp_base),
                    "meal_allowance": int(emp_meal),
                    "transport":    int(emp_trans),
                    "email":        emp_email.strip(),
                    "id_number":    emp_idnum.strip(),
                    "join_date":    emp_join.strip(),
                    "is_active":    1,
                    "note":         emp_note.strip(),
                }
                eid = upsert_employee(data)
                st.success(f"✅ 직원 저장 완료 (ID: {eid})")
                st.rerun()

    # ── 엑셀 일괄 등록 ───────────────────────────────────────
    with tab_import:
        st.markdown("""
        **엑셀 양식 구조**
        - **시트1 (4대보험가입자)**: 직원명, 소속지점, 입사일, 부양가족수, 세전기본급, 식대, 교통비, 이메일, 비고
        - **시트2 (사업소득자)**: 직원명, 소속지점, 등록일, 주민등록번호, 이메일, 비고
        """)

        uploaded = st.file_uploader("직원마스터_초기데이터.xlsx", type=["xlsx"], key="emp_bulk_upload")
        if uploaded and st.button("일괄 등록", type="primary", key="emp_bulk_btn"):
            with st.spinner("처리 중..."):
                saved, errors = import_employees_from_excel(uploaded)
            st.success(f"✅ {saved}명 등록 완료")
            if errors:
                for e in errors:
                    st.warning(e)
            st.rerun()
