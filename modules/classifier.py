import sqlite3
import pandas as pd
from modules.db import get_conn


def _get_rules(bank: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT keyword, branch, category, hit_count FROM keyword_rules WHERE bank=? ORDER BY hit_count DESC",
        (bank,)
    ).fetchall()
    conn.close()
    return [{"keyword": r[0], "branch": r[1], "category": r[2], "hit_count": r[3]} for r in rows]


def classify_transactions(df: pd.DataFrame, bank: str) -> pd.DataFrame:
    """
    이미 branch/category가 채워진 행은 그대로 두고,
    비어있는 행만 키워드 매칭으로 자동 분류.
    매칭 안 되면 needs_review=1.
    """
    rules = _get_rules(bank)

    for idx, row in df.iterrows():
        # branch와 category 모두 비어있지 않을 때만 스킵 (빈 문자열은 미분류로 처리)
        branch_filled = bool(str(row.get("branch", "")).strip())
        cat_filled    = bool(str(row.get("category", "")).strip())
        if branch_filled and cat_filled:
            continue  # 이미 분류됨

        keyword_col = "description"
        text = str(row.get(keyword_col, ""))

        matched = False
        for rule in rules:
            if rule["keyword"] in text:
                df.at[idx, "branch"] = rule["branch"]
                df.at[idx, "category"] = rule["category"]
                df.at[idx, "is_excluded"] = 1 if rule["category"] == "제외" else 0
                df.at[idx, "needs_review"] = 0
                matched = True
                break

        if not matched:
            df.at[idx, "needs_review"] = 1

    return df


def add_rule(bank: str, keyword: str, branch: str, category: str):
    conn = get_conn()
    conn.execute("""
        INSERT INTO keyword_rules (bank, keyword, branch, category, hit_count)
        VALUES (?, ?, ?, ?, 1)
        ON CONFLICT(bank, keyword, branch, category) DO UPDATE SET hit_count = hit_count + 1
    """, (bank, keyword, branch, category))
    conn.commit()
    conn.close()


def get_all_rules(bank: str = None) -> pd.DataFrame:
    conn = get_conn()
    if bank:
        df = pd.read_sql("SELECT * FROM keyword_rules WHERE bank=? ORDER BY hit_count DESC", conn, params=(bank,))
    else:
        df = pd.read_sql("SELECT * FROM keyword_rules ORDER BY bank, hit_count DESC", conn)
    conn.close()
    return df
