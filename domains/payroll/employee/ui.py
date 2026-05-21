"""
domains/payroll/employee/ui.py — 직원 마스터 관리 UI
"""
import streamlit as st
import pandas as pd

from shared.utils import sec
from domains.branch.db import get_active_branch_names
from domains.payroll.db import (
    get_all_employees, get_employees_by_branch,
    upsert_employee, delete_employee,
)
from domains.payroll.employee.service import import_employees_from_excel

EMP_TYPE_LABELS = {
    "insured":    "4대보험 가입자",
    "freelance":  "사업소득자 (3.3%)",
    "business":   "일반사업자",
    "tax_exempt": "면세사업자",
}
EMP_TYPE_SHORT = {
    "insured":    "4대보험",
    "freelance":  "사업소득자",
    "business":   "일반사업자",
    "tax_exempt": "면세사업자",
}


def render():
    BRANCH_LIST = get_active_branch_names()
    sec("직원 마스터")

    tab_list, tab_add, tab_import = st.tabs(["직원 목록", "직원 추가/수정", "엑셀 일괄 등록"])

    # ── 직원 목록 ────────────────────────────────────────────
    with tab_list:
        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
        sel_br   = col_f1.selectbox("지점 필터", ["전체"] + BRANCH_LIST, key="emp_br_filter")
        type_filter = col_f2.selectbox("유형 필터", ["전체", "4대보험", "사업소득자", "사업자"],
                                       key="emp_type_filter")
        show_all = col_f3.checkbox("퇴직자 포함", value=False, key="emp_show_all")

        if sel_br == "전체":
            emps = get_all_employees(active_only=not show_all)
        else:
            emps = get_employees_by_branch(sel_br, active_only=not show_all)

        if type_filter == "4대보험":
            emps = [e for e in emps if e["emp_type"] == "insured"]
        elif type_filter == "사업소득자":
            emps = [e for e in emps if e["emp_type"] == "freelance"]
        elif type_filter == "사업자":
            emps = [e for e in emps if e["emp_type"] in ("business", "tax_exempt")]

        if not emps:
            st.info("등록된 직원/사업자가 없습니다.")
        else:
            df = pd.DataFrame(emps)
            display_cols = {
                "id": "ID", "name": "이름", "branch": "지점",
                "emp_type": "유형", "dependents": "부양가족",
                "base_salary": "기본급", "meal_allowance": "식대",
                "transport": "교통비", "email": "이메일",
                "join_date": "입사/등록일", "is_active": "재직",
            }
            # 수정 가능한 편집용 df (숫자 그대로 유지)
            edit_df = df[[c for c in display_cols if c in df.columns]].copy()
            edit_df = edit_df.rename(columns=display_cols)
            edit_df["유형"] = edit_df["유형"].map(EMP_TYPE_SHORT).fillna(edit_df["유형"])
            edit_df["재직"] = edit_df["재직"].apply(lambda v: bool(v))
            for col in ["부양가족", "기본급", "식대", "교통비"]:
                if col in edit_df.columns:
                    edit_df[col] = pd.to_numeric(edit_df[col], errors="coerce").fillna(0).astype(int)

            edited = st.data_editor(
                edit_df,
                use_container_width=True,
                hide_index=True,
                height=450,
                num_rows="fixed",
                key="emp_editor_table",
                column_config={
                    "ID":       st.column_config.NumberColumn("ID", disabled=True, width="small"),
                    "이름":     st.column_config.TextColumn("이름", width="medium"),
                    "지점":     st.column_config.SelectboxColumn("지점", options=BRANCH_LIST),
                    "유형":     st.column_config.SelectboxColumn("유형", options=list(EMP_TYPE_SHORT.values())),
                    "부양가족": st.column_config.NumberColumn("부양가족", min_value=0, max_value=10, step=1),
                    "기본급":   st.column_config.NumberColumn("기본급", format="%d", min_value=0),
                    "식대":     st.column_config.NumberColumn("식대", format="%d", min_value=0),
                    "교통비":   st.column_config.NumberColumn("교통비", format="%d", min_value=0),
                    "이메일":   st.column_config.TextColumn("이메일"),
                    "입사/등록일": st.column_config.TextColumn("입사/등록일"),
                    "재직":     st.column_config.CheckboxColumn("재직"),
                },
            )
            st.caption(f"총 {len(emps)}명 · 셀을 클릭해 직접 수정 후 아래 저장 버튼을 누르세요.")

            if st.button("💾 변경사항 저장", key="emp_inline_save", type="primary"):
                changes = st.session_state.get("emp_editor_table", {}).get("edited_rows", {})
                if not changes:
                    st.info("변경된 내용이 없습니다.")
                else:
                    type_reverse = {v: k for k, v in EMP_TYPE_SHORT.items()}
                    col_reverse  = {v: k for k, v in display_cols.items()}
                    saved_count  = 0
                    for row_idx_str, row_changes in changes.items():
                        emp = dict(emps[int(row_idx_str)])
                        for col_label, val in row_changes.items():
                            db_col = col_reverse.get(col_label)
                            if not db_col:
                                continue
                            if db_col == "emp_type":
                                emp[db_col] = type_reverse.get(val, val)
                            elif db_col == "is_active":
                                emp[db_col] = 1 if val else 0
                            elif db_col in ("base_salary", "meal_allowance", "transport", "dependents"):
                                emp[db_col] = int(val or 0)
                            else:
                                emp[db_col] = str(val or "").strip()
                        upsert_employee(emp)
                        saved_count += 1
                    st.success(f"✅ {saved_count}명 수정 완료")
                    st.rerun()

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
        emp_name = col2.text_input("이름 / 상호 *", key="emp_name")
        emp_br   = col3.selectbox("소속지점 *", BRANCH_LIST, key="emp_branch")

        col4, col5 = st.columns(2)
        emp_type = col4.selectbox(
            "유형 *",
            ["insured", "freelance", "business", "tax_exempt"],
            format_func=lambda x: EMP_TYPE_LABELS[x],
            key="emp_type",
        )
        emp_join = col5.text_input("입사/등록일 (YYYY-MM-DD)", key="emp_join")

        is_insured  = emp_type == "insured"
        is_business = emp_type in ("business", "tax_exempt")

        if is_insured:
            col6, col7, col8, col9 = st.columns(4)
            emp_dep   = col6.number_input("부양가족수 (본인 포함)", min_value=0, max_value=10, value=1, key="emp_dep")
            emp_base  = col7.number_input("세전기본급", min_value=0, step=10000, key="emp_base")
            emp_meal  = col8.number_input("식대", min_value=0, step=10000, value=100000, key="emp_meal")
            emp_trans = col9.number_input("교통비", min_value=0, step=10000, key="emp_trans")
        else:
            emp_dep   = 0
            emp_base  = 0
            emp_meal  = 0
            emp_trans = 0

        col10, col11 = st.columns(2)
        emp_email = col10.text_input("이메일", key="emp_email")
        if is_business:
            emp_idnum = col11.text_input("사업자등록번호", key="emp_idnum",
                                         help="계산서 발행 확인용")
        elif emp_type == "freelance":
            emp_idnum = col11.text_input("주민등록번호", type="password", key="emp_idnum",
                                          help="원천징수영수증 발급용")
        else:
            emp_idnum = ""

        emp_note = st.text_input("비고", key="emp_note")

        # 사업자 유형 안내
        if is_business:
            st.info(
                f"{'📄 일반사업자' if emp_type == 'business' else '📄 면세사업자'}: "
                "계산서 발행 기준으로 지급 처리됩니다. 별도 세금 공제 없음."
            )

        if st.button("저장", type="primary", key="emp_save_btn"):
            if not emp_name or not emp_br:
                st.error("이름과 지점은 필수입니다.")
            else:
                data = {
                    "id":             int(emp_id) if emp_id else None,
                    "name":           emp_name.strip(),
                    "branch":         emp_br,
                    "emp_type":       emp_type,
                    "dependents":     int(emp_dep),
                    "base_salary":    int(emp_base),
                    "meal_allowance": int(emp_meal),
                    "transport":      int(emp_trans),
                    "email":          emp_email.strip(),
                    "id_number":      emp_idnum.strip() if emp_idnum else "",
                    "join_date":      emp_join.strip(),
                    "is_active":      1,
                    "note":           emp_note.strip(),
                }
                eid = upsert_employee(data)
                st.success(f"✅ 저장 완료 (ID: {eid})")
                st.rerun()

    # ── 엑셀 일괄 등록 ───────────────────────────────────────
    with tab_import:
        st.markdown("""
        **엑셀 양식 구조**
        - **시트1 (4대보험가입자)**: 직원명, 소속지점, 입사일, 부양가족수, 세전기본급, 식대, 교통비, 이메일, 비고
        - **시트2 (사업소득자)**: 직원명, 소속지점, 등록일, 주민등록번호, 이메일, 비고
        - **시트3 (사업자)**: 상호명, 소속지점, 사업자구분(일반/면세), 사업자등록번호, 이메일, 비고
        """)

        uploaded = st.file_uploader("직원마스터_초기데이터.xlsx", type=["xlsx"], key="emp_bulk_upload")
        if uploaded and st.button("일괄 등록", type="primary", key="emp_bulk_btn"):
            with st.spinner("처리 중..."):
                saved, errors = import_employees_from_excel(uploaded)
            st.success(f"✅ {saved}명/개 등록 완료")
            if errors:
                for e in errors:
                    st.warning(e)
            st.rerun()
