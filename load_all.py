import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
from modules.db import init_db, load_keyword_rules, upsert_card_sales, upsert_bank_transactions, upsert_payroll_freelance, upsert_payroll_insured
from modules.parser import parse_card_sales, parse_hana, parse_shinhan, parse_payroll_freelance, parse_payroll_insured
from modules.classifier import classify_transactions

init_db()
load_keyword_rules()

xl_settle = pd.ExcelFile('정산내역.xlsx')
xl_dash = pd.ExcelFile('지점별 대시보드.xlsx')

YEAR = 2026
MONTHS = [1, 2, 3, 4]

for month in MONTHS:
    print(f'--- {month}월 처리 중 ---')

    # 카드정산
    try:
        df = parse_card_sales(xl_settle, YEAR, month)
        upsert_card_sales(df, YEAR, month)
        print(f'  카드정산: {len(df)}건')
    except Exception as e:
        print(f'  카드정산 오류: {e}')

    # 하나통장
    try:
        df = parse_hana(xl_settle, YEAR, month)
        df = classify_transactions(df, 'hana')
        upsert_bank_transactions(df, 'hana', YEAR, month)
        print(f'  하나통장: {len(df)}건 (미분류 {int(df["needs_review"].sum())}건)')
    except Exception as e:
        print(f'  하나통장 오류: {e}')

    # 신한통장
    try:
        df = parse_shinhan(xl_settle, YEAR, month)
        df = classify_transactions(df, 'shinhan')
        upsert_bank_transactions(df, 'shinhan', YEAR, month)
        print(f'  신한통장: {len(df)}건 (미분류 {int(df["needs_review"].sum())}건)')
    except Exception as e:
        print(f'  신한통장 오류: {e}')

    # 사업소득자 (프리랜서 인건비)
    try:
        df = parse_payroll_freelance(xl_dash, YEAR, month)
        upsert_payroll_freelance(df, YEAR, month)
        print(f'  사업소득자: {len(df)}개 지점')
    except Exception as e:
        print(f'  사업소득자 오류: {e}')

    # 지점별집계 (4대보험 직원)
    try:
        df = parse_payroll_insured(xl_dash, YEAR, month)
        upsert_payroll_insured(df, YEAR, month)
        print(f'  지점별집계: {len(df)}개 지점')
    except Exception as e:
        print(f'  지점별집계 오류: {e}')

print()
print('=== 완료 ===')

# 저장 확인
import sqlite3
from modules.db import get_conn
conn = get_conn()
for table in ['card_sales','bank_transactions','payroll_freelance','payroll_insured']:
    cnt = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {cnt}건')
conn.close()
