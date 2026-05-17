import pandas as pd
import json
from pathlib import Path

MAPPING_PATH = Path(__file__).parent.parent / "mapping" / "branch_mapping.json"


def _load_branch_mapping() -> dict:
    with open(MAPPING_PATH, encoding="utf-8") as f:
        return json.load(f)["card_merchant_to_branch"]


def _to_int(val) -> int:
    try:
        return int(float(str(val).replace(",", "")))
    except Exception:
        return 0


# ── 카드사 결과 집계 조회 (월별 파일) ────────────────────────
# 컬럼 구조: O=합계금액, P=수수료, Q=입금액, S=가맹점명 (위치로 고정하지 않고 헤더명으로 탐지)

def _find_col(header_list: list, keywords: list, fallback: int) -> int:
    """헤더 목록에서 keyword를 포함하는 첫 번째 컬럼 인덱스 반환. 없으면 fallback."""
    for kw in keywords:
        for i, h in enumerate(header_list):
            if kw in str(h).strip():
                return i
    return fallback


def _find_header_row(filepath: str, search_kws=('가맹점', '합계금액', '수수료')) -> int:
    """헤더 행 번호 자동 탐지 (상위 10행 스캔)."""
    probe = pd.read_excel(filepath, header=None, dtype=str, nrows=10)
    for i, row in probe.iterrows():
        vals = [str(v).strip() for v in row if pd.notna(v)]
        if sum(1 for v in vals if any(k in v for k in search_kws)) >= 2:
            return i
    return 0


def parse_card_aggregate(filepath: str, year: int, month: int) -> pd.DataFrame:
    merchant_map = _load_branch_mapping()

    header_row = _find_header_row(filepath)
    df = pd.read_excel(filepath, header=header_row, dtype=str)
    n = len(df.columns)
    hdrs = [str(c).strip() for c in df.columns]

    # 컬럼 위치를 헤더명으로 탐지 → 없으면 원래 고정 인덱스로 fallback
    c_merchant = _find_col(hdrs, ['가맹점명', '가맹점 명', '가맹점'], min(18, n-1))
    c_total    = _find_col(hdrs, ['합계금액', '총금액', '합  계금액'], min(14, n-1))
    c_fee      = _find_col(hdrs, ['수수료'], min(15, n-1))
    c_date     = _find_col(hdrs, ['청구일', '입금일', '매입일'], min(4, n-1))
    c_company  = _find_col(hdrs, ['매입사', '카드사'], min(1, n-1))

    df.columns = range(n)

    rows = []
    for _, row in df.iterrows():
        merchant     = str(row.iloc[c_merchant]).strip()
        total_amount = _to_int(row.iloc[c_total])
        fee          = _to_int(row.iloc[c_fee])

        if total_amount == 0 or merchant in ('nan', '', 'None'):
            continue

        vat           = total_amount // 11
        supply_amount = total_amount - vat
        net_amount    = supply_amount - fee
        branch        = merchant_map.get(merchant, "미매핑")

        rows.append({
            "branch":         branch,
            "raw_merchant":   merchant,
            "card_company":   str(row.iloc[c_company]).strip() if pd.notna(row.iloc[c_company]) else "",
            "total_amount":   total_amount,
            "vat":            vat,
            "supply_amount":  supply_amount,
            "fee":            fee,
            "net_amount":     net_amount,
            "sale_date":      str(row.iloc[c_date]).strip() if pd.notna(row.iloc[c_date]) else "",
        })

    return pd.DataFrame(rows)


# ── 신용카드 파일 ────────────────────────────────────────
# 컬럼: 가맹점명(A) 거래일자(B) 거래금액(G) 공급가액(H) 부가세(I) 수수료(L)

def parse_credit_card(filepath: str, year: int, month: int) -> pd.DataFrame:
    merchant_map = _load_branch_mapping()

    header_row = _find_header_row(filepath, search_kws=('가맹점', '거래금액', '공급가액', '부가세'))
    df = pd.read_excel(filepath, header=header_row, dtype=str)
    n = len(df.columns)
    hdrs = [str(c).strip() for c in df.columns]

    c_merchant = _find_col(hdrs, ['가맹점명', '가맹점'], min(0, n-1))
    c_total    = _find_col(hdrs, ['거래금액', '총금액'], min(6, n-1))
    c_supply   = _find_col(hdrs, ['공급가액', '공급금액'], min(7, n-1))
    c_vat      = _find_col(hdrs, ['부가세', '부가가치세'], min(8, n-1))
    c_fee      = _find_col(hdrs, ['수수료'], min(11, n-1))
    c_date     = _find_col(hdrs, ['거래일자', '거래일', '매입일'], min(1, n-1))

    df.columns = range(n)

    rows = []
    for _, row in df.iterrows():
        merchant      = str(row.iloc[c_merchant]).strip()
        total_amount  = _to_int(row.iloc[c_total])
        supply_amount = _to_int(row.iloc[c_supply])
        vat           = _to_int(row.iloc[c_vat])
        fee           = _to_int(row.iloc[c_fee])
        net_amount    = supply_amount - fee
        branch        = merchant_map.get(merchant, "미매핑")

        if total_amount == 0 or merchant in ('nan', '', 'None'):
            continue

        rows.append({
            "branch":        branch,
            "raw_merchant":  merchant,
            "card_company":  "",
            "total_amount":  total_amount,
            "vat":           vat,
            "supply_amount": supply_amount,
            "fee":           fee,
            "net_amount":    net_amount,
            "sale_date":     str(row.iloc[c_date]).strip() if pd.notna(row.iloc[c_date]) else "",
        })

    return pd.DataFrame(rows)


# ── 하나 통장 ─────────────────────────────────────────────
# 컬럼: No 거래일시 적요 의뢰인/수취인 입금 출금 거래후잔액 지점 내용 계정과목

def parse_hana(xl: pd.ExcelFile, year: int, month: int) -> pd.DataFrame:
    df = xl.parse(sheet_name=1, header=0)
    df.columns = ["no", "tx_date", "description", "counterpart",
                  "deposit", "withdrawal", "balance", "branch", "content", "category"]

    df["tx_date"] = pd.to_datetime(df["tx_date"], errors="coerce")
    df = df[(df["tx_date"].dt.year == year) & (df["tx_date"].dt.month == month)].copy()

    for col in ["deposit", "withdrawal", "balance"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["category"] = df["category"].apply(_normalize_category)
    df["vat"] = df.apply(
        lambda r: r["deposit"] // 11 if _is_revenue_cat(r["category"]) and r["deposit"] > 0 else 0,
        axis=1
    )
    df["is_excluded"] = (df["category"] == "제외").astype(int)
    df["needs_review"] = (df["branch"].isna() | df["category"].isna() | (df["category"] == "")).astype(int)
    df["tx_date"] = df["tx_date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    return df[["tx_date", "description", "counterpart", "deposit", "withdrawal",
               "balance", "branch", "content", "category", "vat", "is_excluded", "needs_review"]]


# ── 신한 통장 ─────────────────────────────────────────────
# 컬럼: No 전체선택 거래일시 적요 입금액 출금액 내용 잔액 거래점명 입금인코드 메모 _ 지점 내용.1 계정과목

def parse_shinhan(xl: pd.ExcelFile, year: int, month: int) -> pd.DataFrame:
    df = xl.parse(sheet_name=2, header=0)
    # 파일 컬럼 수에 맞게 동적으로 이름 지정 (뒤쪽 빈 열 무시)
    base_cols = ["no", "select", "tx_date", "description", "deposit", "withdrawal",
                 "content_raw", "balance", "branch_name", "depositor_code", "memo",
                 "dummy", "branch", "content", "category"]
    extra = [f"_ex{i}" for i in range(len(df.columns) - len(base_cols))]
    df.columns = base_cols + extra

    df["tx_date"] = pd.to_datetime(df["tx_date"], errors="coerce")
    df = df[(df["tx_date"].dt.year == year) & (df["tx_date"].dt.month == month)].copy()

    for col in ["deposit", "withdrawal", "balance"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["description"] = df["content_raw"].fillna(df["description"])
    df["counterpart"] = df["depositor_code"].fillna("").astype(str)
    df["category"] = df["category"].apply(_normalize_category)
    df["vat"] = df.apply(
        lambda r: r["deposit"] // 11 if _is_revenue_cat(r["category"]) and r["deposit"] > 0 else 0,
        axis=1
    )
    df["is_excluded"] = (df["category"] == "제외").astype(int)
    df["needs_review"] = (df["branch"].isna() | df["category"].isna() | (df["category"] == "")).astype(int)
    df["tx_date"] = df["tx_date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    return df[["tx_date", "description", "counterpart", "deposit", "withdrawal",
               "balance", "branch", "content", "category", "vat", "is_excluded", "needs_review"]]


# ── 인건비 ────────────────────────────────────────────────

def parse_payroll_freelance(xl: pd.ExcelFile, year: int, month: int) -> pd.DataFrame:
    """사업소득자 탭 → type='freelance'"""
    df_raw = xl.parse("사업소득자", header=None)
    # 월별 5컬럼씩: 총지급액, 소득세, 지방세, 소득세+주민세, 실지급액
    col = 1 + (month - 1) * 5

    rows = []
    for i in range(2, len(df_raw)):
        branch = df_raw.iloc[i, 0]
        if pd.isna(branch):
            continue
        gross   = _to_int(df_raw.iloc[i, col])
        inc_tax = _to_int(df_raw.iloc[i, col + 1])
        loc_tax = _to_int(df_raw.iloc[i, col + 2])
        tax_tot = _to_int(df_raw.iloc[i, col + 3])
        net     = _to_int(df_raw.iloc[i, col + 4])
        rows.append({
            "branch": str(branch),
            "gross_pay": gross,
            "net_pay": net,
            "insurance": 0,
            "income_tax": inc_tax,
            "local_tax": loc_tax,
            "headcount": 0,
        })
    return pd.DataFrame(rows)


def parse_payroll_insured(xl: pd.ExcelFile, year: int, month: int) -> pd.DataFrame:
    """지점별집계 탭 → type='insured'"""
    df_raw = xl.parse("지점별집계", header=None)
    # 월별 4컬럼씩: 인원, 실지급액, 4대보험공제, 소득세·지방세
    col = 1 + (month - 1) * 4

    rows = []
    for i in range(2, len(df_raw)):
        branch = df_raw.iloc[i, 0]
        if pd.isna(branch):
            continue
        headcount = _to_int(df_raw.iloc[i, col])
        net       = _to_int(df_raw.iloc[i, col + 1])
        insurance = _to_int(df_raw.iloc[i, col + 2])
        inc_tax   = _to_int(df_raw.iloc[i, col + 3])
        rows.append({
            "branch": str(branch),
            "gross_pay": net + insurance + inc_tax,
            "net_pay": net,
            "insurance": insurance,
            "income_tax": inc_tax,
            "local_tax": 0,
            "headcount": headcount,
        })
    return pd.DataFrame(rows)


# ── 내부 유틸 ─────────────────────────────────────────────

def _normalize_category(cat) -> str:
    if pd.isna(cat):
        return ""
    cat = str(cat).strip()
    mapping = {
        "GX매출":    "기타매출(현금)",
        "PT매출":    "기타매출(현금)",
        "기타매출":  "기타매출(현금)",
        "카드매출":  "기타매출(카드)",
        "골프매출":  "골프매출(현금)",
        "키즈매출":  "키즈매출(현금)",
        "소득세·지방세": "소득세·지방세 합계",
        "소득세지방세":  "소득세·지방세 합계",
    }
    return mapping.get(cat, cat)


_REVENUE_CATS = {
    "기타매출(현금)", "PT매출(현금)", "GX매출(현금)",
    "골프매출(현금)", "키즈매출(현금)", "도급비", "시설상환비", "카페매출",
    "기타매출(카드)",
}


def _is_revenue_cat(cat: str) -> bool:
    return cat in _REVENUE_CATS
