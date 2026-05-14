import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "settlement.db"

# 대시보드 기준 계정과목 체계
REVENUE_CATEGORIES = {
    "카드": ["PT매출(카드)", "GX매출(카드)", "골프매출(카드)", "키즈매출(카드)", "기타매출(카드)"],
    "현금": ["PT매출(현금)", "GX매출(현금)", "골프매출(현금)", "키즈매출(현금)", "기타매출(현금)"],
    "기타": ["도급비", "시설상환비", "카페매출"],
}
EXPENSE_CATEGORIES = [
    "급여", "4대보험료", "소득세·지방세 합계", "프리랜서", "퇴직금",
    "기타세금", "부가세", "카드수수료", "법인카드", "환불",
    "렌탈비", "관리비", "임차료", "비품구매", "기타지출",
    "운영경비", "외주용역비", "감가상각비", "기타보험료",
    "복리후생비", "이자비용", "AS비용", "차량유지비",
]


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS card_sales (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            year           INTEGER,
            month          INTEGER,
            source         TEXT,
            branch         TEXT,
            raw_merchant   TEXT,
            card_company   TEXT,
            total_amount   INTEGER DEFAULT 0,
            vat            INTEGER DEFAULT 0,
            supply_amount  INTEGER DEFAULT 0,
            fee            INTEGER DEFAULT 0,
            net_amount     INTEGER DEFAULT 0,
            sale_date      TEXT
        );

        CREATE TABLE IF NOT EXISTS bank_transactions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            year         INTEGER,
            month        INTEGER,
            bank         TEXT,
            tx_date      TEXT,
            description  TEXT,
            counterpart  TEXT,
            deposit      INTEGER DEFAULT 0,
            withdrawal   INTEGER DEFAULT 0,
            balance      INTEGER DEFAULT 0,
            branch       TEXT,
            content      TEXT,
            category     TEXT,
            vat          INTEGER DEFAULT 0,
            is_excluded  INTEGER DEFAULT 0,
            needs_review INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS payroll (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            year            INTEGER,
            month           INTEGER,
            branch          TEXT,
            type            TEXT,   -- 'insured' | 'freelance'
            gross_pay       INTEGER DEFAULT 0,
            net_pay         INTEGER DEFAULT 0,
            insurance       INTEGER DEFAULT 0,
            income_tax      INTEGER DEFAULT 0,
            local_tax       INTEGER DEFAULT 0,
            headcount       INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS keyword_rules (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            bank       TEXT,
            keyword    TEXT,
            branch     TEXT,
            category   TEXT,
            hit_count  INTEGER DEFAULT 0,
            UNIQUE(bank, keyword, branch, category)
        );
    """)
    # 기존 테이블이 있으면 vat 컬럼 추가 (마이그레이션)
    for col_def in [
        ("bank_transactions", "vat", "INTEGER DEFAULT 0"),
        ("card_sales", "source", "TEXT"),
        ("card_sales", "total_amount", "INTEGER DEFAULT 0"),
        ("card_sales", "vat", "INTEGER DEFAULT 0"),
        ("card_sales", "supply_amount", "INTEGER DEFAULT 0"),
        ("card_sales", "fee", "INTEGER DEFAULT 0"),
        ("card_sales", "net_amount", "INTEGER DEFAULT 0"),
    ]:
        try:
            c.execute(f"ALTER TABLE {col_def[0]} ADD COLUMN {col_def[1]} {col_def[2]}")
        except Exception:
            pass
    conn.commit()
    conn.close()


def load_keyword_rules():
    import json
    rules_path = Path(__file__).parent.parent / "mapping" / "keyword_rules.json"
    if not rules_path.exists():
        return
    with open(rules_path, encoding="utf-8") as f:
        data = json.load(f)
    conn = get_conn()
    c = conn.cursor()
    for bank, key in [("hana", "hana"), ("shinhan", "shinhan")]:
        for rule in data.get(key, []):
            # 계정과목 정규화
            cat = _normalize_category(rule["category"])
            c.execute("""
                INSERT OR IGNORE INTO keyword_rules (bank, keyword, branch, category, hit_count)
                VALUES (?, ?, ?, ?, ?)
            """, (bank, rule["keyword"], rule["branch"], cat, rule.get("count", 0)))
    conn.commit()
    conn.close()


def _normalize_category(cat: str) -> str:
    """기존 계정과목을 대시보드 기준으로 정규화"""
    mapping = {
        "GX매출": "기타매출(현금)",
        "PT매출": "기타매출(현금)",
        "기타매출": "기타매출(현금)",
        "카드매출": "기타매출(카드)",
        "골프매출": "골프매출(현금)",
        "키즈매출": "키즈매출(현금)",
        "4대보험료": "4대보험료",
        "소득세·지방세": "소득세·지방세 합계",
        "소득세지방세": "소득세·지방세 합계",
    }
    return mapping.get(cat, cat)


# ── 카드 매출 ─────────────────────────────────────────────

def upsert_card_sales(df: pd.DataFrame, source: str, year: int, month: int):
    conn = get_conn()
    conn.execute(
        "DELETE FROM card_sales WHERE source=? AND year=? AND month=?",
        (source, year, month)
    )
    df = df.copy()
    df["source"] = source
    df["year"] = year
    df["month"] = month
    df.to_sql("card_sales", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def get_card_by_branch(year: int, month: int = None):
    conn = get_conn()
    mf = "AND month=:month" if month else ""
    params = {"year": year}
    if month:
        params["month"] = month
    df = pd.read_sql(f"""
        SELECT branch,
               SUM(total_amount)  as card_total,
               SUM(vat)           as card_vat,
               SUM(supply_amount) as card_supply,
               SUM(fee)           as card_fee,
               SUM(net_amount)    as card_net
        FROM card_sales
        WHERE year=:year {mf}
        GROUP BY branch
    """, conn, params=params)
    conn.close()
    return df


# ── 통장 거래 ─────────────────────────────────────────────

def upsert_bank_transactions(df: pd.DataFrame, bank: str, year: int, month: int):
    conn = get_conn()
    conn.execute(
        "DELETE FROM bank_transactions WHERE bank=? AND year=? AND month=?",
        (bank, year, month)
    )
    df = df.copy()
    df["bank"] = bank
    df["year"] = year
    df["month"] = month
    df.to_sql("bank_transactions", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def get_branch_cash_revenue(year: int, month: int = None):
    """통장 현금 매출: 공급가액(deposit - vat)과 VAT 반환"""
    conn = get_conn()
    mf = "AND month=:month" if month else ""
    params = {"year": year}
    if month:
        params["month"] = month
    revenue_cats = (
        "'기타매출(현금)','PT매출(현금)','GX매출(현금)',"
        "'골프매출(현금)','키즈매출(현금)','도급비','시설상환비','카페매출'"
    )
    df = pd.read_sql(f"""
        SELECT branch,
               SUM(deposit - vat) as cash_supply,
               SUM(vat)           as cash_vat,
               SUM(deposit)       as cash_total
        FROM bank_transactions
        WHERE year=:year {mf}
          AND is_excluded=0
          AND category IN ({revenue_cats})
          AND deposit > 0
        GROUP BY branch
    """, conn, params=params)
    conn.close()
    return df


def get_expense_by_category(year: int, month: int = None, branch: str = None):
    conn = get_conn()
    filters = ["year=:year", "is_excluded=0", "withdrawal > 0"]
    params = {"year": year}
    if month:
        filters.append("month=:month")
        params["month"] = month
    if branch:
        filters.append("branch=:branch")
        params["branch"] = branch
    where = " AND ".join(filters)
    df = pd.read_sql(f"""
        SELECT branch, month, category, SUM(withdrawal) as amount, SUM(vat) as vat
        FROM bank_transactions
        WHERE {where}
        GROUP BY branch, month, category
    """, conn, params=params)
    conn.close()
    return df


def get_unreviewed_transactions():
    conn = get_conn()
    df = pd.read_sql(
        "SELECT * FROM bank_transactions WHERE needs_review=1 ORDER BY year, month, tx_date",
        conn
    )
    conn.close()
    return df


def update_transaction_classification(tx_id: int, branch: str, category: str):
    conn = get_conn()
    conn.execute(
        "UPDATE bank_transactions SET branch=?, category=?, needs_review=0 WHERE id=?",
        (branch, category, tx_id)
    )
    conn.commit()
    conn.close()


# ── 인건비 ───────────────────────────────────────────────

def upsert_payroll(df: pd.DataFrame, year: int, month: int, pay_type: str):
    conn = get_conn()
    conn.execute(
        "DELETE FROM payroll WHERE year=? AND month=? AND type=?",
        (year, month, pay_type)
    )
    df = df.copy()
    df["year"] = year
    df["month"] = month
    df["type"] = pay_type
    df.to_sql("payroll", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def get_payroll_summary(year: int, month: int = None, branch: str = None):
    conn = get_conn()
    filters = ["year=:year"]
    params = {"year": year}
    if month:
        filters.append("month=:month")
        params["month"] = month
    if branch:
        filters.append("branch=:branch")
        params["branch"] = branch
    where = " AND ".join(filters)
    df = pd.read_sql(f"""
        SELECT branch, month, type,
               SUM(gross_pay)  as gross_pay,
               SUM(net_pay)    as net_pay,
               SUM(insurance)  as insurance,
               SUM(income_tax) as income_tax,
               SUM(local_tax)  as local_tax,
               SUM(headcount)  as headcount
        FROM payroll
        WHERE {where}
        GROUP BY branch, month, type
    """, conn, params=params)
    conn.close()
    return df


def get_keyword_rules(bank: str = None):
    conn = get_conn()
    if bank:
        df = pd.read_sql(
            "SELECT * FROM keyword_rules WHERE bank=? ORDER BY hit_count DESC",
            conn, params=(bank,)
        )
    else:
        df = pd.read_sql(
            "SELECT * FROM keyword_rules ORDER BY bank, hit_count DESC", conn
        )
    conn.close()
    return df
