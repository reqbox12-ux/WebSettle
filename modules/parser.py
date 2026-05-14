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
# 컬럼: No(0) 매입사(1) 사업자번호(2) IND(3) 청구일(4) 입금일(5) 계좌번호(6)
#        접수건(7) 접수금액(8) 반송건(9) 반송금액(10) 보류건(11) 보류금액(12)
#        합계건(13) O=합계금액(14) P=수수료(15) Q=입금액(16) 가맹점번호(17) S=가맹점명(18)

def parse_card_aggregate(filepath: str, year: int, month: int) -> pd.DataFrame:
    merchant_map = _load_branch_mapping()
    df = pd.read_excel(filepath, header=0, dtype=str)

    # 헤더 행 기준으로 열 인덱스 사용 (이름이 달라도 위치로)
    cols = list(df.columns)
    # O=14, P=15, Q=16, S=18  (0-based after header)
    df.columns = range(len(cols))

    rows = []
    for _, row in df.iterrows():
        merchant = str(row[18]).strip()
        total_amount = _to_int(row[14])   # O열: 합계금액
        fee          = _to_int(row[15])   # P열: 수수료
        vat          = total_amount // 11  # 부가세 = 합계 / 11
        supply_amount = total_amount - vat # 공급가액 = 합계 - 부가세
        net_amount    = supply_amount - fee # 실수령 = 공급가액 - 수수료
        branch = merchant_map.get(merchant, "미매핑")

        if total_amount == 0:
            continue

        rows.append({
            "branch": branch,
            "raw_merchant": merchant,
            "card_company": str(row[1]).strip() if pd.notna(row[1]) else "",
            "total_amount": total_amount,
            "vat": vat,
            "supply_amount": supply_amount,
            "fee": fee,
            "net_amount": net_amount,
            "sale_date": str(row[4]).strip() if pd.notna(row[4]) else "",
        })

    return pd.DataFrame(rows)


# ── 신용카드 파일 ────────────────────────────────────────
# 컬럼: A=가맹점명(0) 거래일자(1) 가맹점번호(2) 단말기번호(3) 카드번호(4)
#        승인번호(5) 거래금액(6) 공급가액(7) I=부가세(8) 과세(9) 비과세(10)
#        L=수수료(11) 수수료율(12) N=입금예정액(13)

def parse_credit_card(filepath: str, year: int, month: int) -> pd.DataFrame:
    merchant_map = _load_branch_mapping()
    df = pd.read_excel(filepath, header=0, dtype=str)
    df.columns = range(len(df.columns))

    rows = []
    for _, row in df.iterrows():
        merchant      = str(row[0]).strip()
        total_amount  = _to_int(row[6])        # G열: 거래금액(총액)
        vat           = _to_int(row[8])        # I열: 부가세
        supply_amount = _to_int(row[7])        # H열: 공급가액 = 총액 - 부가세
        fee           = _to_int(row[11])       # L열: 수수료
        net_amount    = supply_amount - fee    # 실수령 = 공급가액 - 수수료
        branch = merchant_map.get(merchant, "미매핑")

        if total_amount == 0:
            continue

        rows.append({
            "branch": branch,
            "raw_merchant": merchant,
            "card_company": "",
            "total_amount": total_amount,
            "vat": vat,
            "supply_amount": supply_amount,
            "fee": fee,
            "net_amount": net_amount,
            "sale_date": str(row[1]).strip() if pd.notna(row[1]) else "",
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
