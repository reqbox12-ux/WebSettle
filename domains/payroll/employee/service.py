"""
domains/payroll/employee/service.py — 직원 마스터 비즈니스 로직
"""
import pandas as pd
from domains.payroll.db import (
    get_all_employees, get_employees_by_branch,
    upsert_employee, delete_employee,
)


def import_employees_from_excel(file) -> tuple[int, list[str]]:
    """
    엑셀 파일에서 직원 초기 데이터 일괄 임포트.
    시트1: 4대보험가입자 / 시트2: 사업소득자
    반환: (저장 수, 오류 목록)
    """
    xl      = pd.ExcelFile(file)
    saved   = 0
    errors  = []

    # 시트1 — 4대보험가입자
    insured_sheets = [s for s in xl.sheet_names if "보험" in s or "4대" in s or "가입자" in s]
    if not insured_sheets:
        insured_sheets = xl.sheet_names[:1]

    for sheet in insured_sheets:
        try:
            df = xl.parse(sheet, dtype=str).fillna("")
            for _, row in df.iterrows():
                name = str(row.get("직원명", "") or row.get("성명", "")).strip()
                if not name:
                    continue
                data = {
                    "name":          name,
                    "branch":        str(row.get("소속지점", "") or row.get("지점", "")).strip(),
                    "emp_type":      "insured",
                    "dependents":    int(str(row.get("부양가족수", 1)).replace(",", "") or 1),
                    "base_salary":   int(str(row.get("세전기본급", 0)).replace(",", "") or 0),
                    "meal_allowance": int(str(row.get("식대", 0)).replace(",", "") or 0),
                    "transport":     int(str(row.get("교통비", 0)).replace(",", "") or 0),
                    "email":         str(row.get("이메일", "")).strip(),
                    "join_date":     str(row.get("입사일", "")).strip(),
                    "note":          str(row.get("비고", "")).strip(),
                    "is_active":     1,
                }
                upsert_employee(data)
                saved += 1
        except Exception as e:
            errors.append(f"[4대보험가입자] {e}")

    # 시트2 — 사업소득자
    freelance_sheets = [s for s in xl.sheet_names if "사업" in s or "프리" in s or "소득자" in s]
    if not freelance_sheets and len(xl.sheet_names) > 1:
        freelance_sheets = xl.sheet_names[1:2]

    for sheet in freelance_sheets:
        try:
            df = xl.parse(sheet, dtype=str).fillna("")
            for _, row in df.iterrows():
                name = str(row.get("직원명", "") or row.get("성명", "")).strip()
                if not name:
                    continue
                data = {
                    "name":      name,
                    "branch":    str(row.get("소속지점", "") or row.get("지점", "")).strip(),
                    "emp_type":  "freelance",
                    "dependents": 0,
                    "base_salary": 0,
                    "meal_allowance": 0,
                    "transport": 0,
                    "email":     str(row.get("이메일", "")).strip(),
                    "id_number": str(row.get("주민등록번호", "")).strip(),
                    "join_date": str(row.get("등록일", "")).strip(),
                    "note":      str(row.get("비고", "")).strip(),
                    "is_active": 1,
                }
                upsert_employee(data)
                saved += 1
        except Exception as e:
            errors.append(f"[사업소득자] {e}")

    return saved, errors
