import sys, os
sys.stdout.reconfigure(encoding='utf-8')

db_path = 'data/settlement.db'
if os.path.exists(db_path):
    os.remove(db_path)

from modules.db import init_db, load_keyword_rules, upsert_card_sales, upsert_bank_transactions, upsert_payroll
from modules.parser import (parse_card_aggregate, parse_credit_card,
                             parse_hana, parse_shinhan,
                             parse_payroll_freelance, parse_payroll_insured)
from modules.classifier import classify_transactions
import pandas as pd

init_db()
load_keyword_rules()

xl_settle = pd.ExcelFile('정산내역.xlsx')
xl_dash   = pd.ExcelFile('지점별 대시보드.xlsx')
YEAR = 2026

for month in [1, 2, 3, 4]:
    print(f'--- {month}월 ---')

    df = parse_card_aggregate(f'카드사 결과 집계 조회{month}월.xlsx', YEAR, month)
    upsert_card_sales(df, 'card_aggregate', YEAR, month)
    sample = df[df['branch'] != '미매핑'].head(1)
    if not sample.empty:
        r = sample.iloc[0]
        print(f'  카드사집계 샘플: 총액={r.total_amount:,} VAT={r.vat:,} 공급={r.supply_amount:,} 수수료={r.fee:,} 실수령={r.net_amount:,}')
    print(f'  카드사집계: {len(df[df["branch"]!="미매핑"])}건')

    df = parse_credit_card(f'신용카드{month}월.xlsx', YEAR, month)
    upsert_card_sales(df, 'credit_card', YEAR, month)
    sample = df[df['branch'] != '미매핑'].head(1)
    if not sample.empty:
        r = sample.iloc[0]
        print(f'  신용카드 샘플: 총액={r.total_amount:,} VAT={r.vat:,} 공급={r.supply_amount:,} 수수료={r.fee:,} 실수령={r.net_amount:,}')
    print(f'  신용카드: {len(df[df["branch"]!="미매핑"])}건')

    df = parse_hana(xl_settle, YEAR, month)
    df = classify_transactions(df, 'hana')
    upsert_bank_transactions(df, 'hana', YEAR, month)
    rev = df[df['deposit']>0]
    if not rev.empty:
        sample = rev.head(1).iloc[0]
        print(f'  하나 현금 샘플: 총액={sample.deposit:,} VAT={sample.vat:,} 공급가액={sample.deposit-sample.vat:,}')

    df = parse_shinhan(xl_settle, YEAR, month)
    df = classify_transactions(df, 'shinhan')
    upsert_bank_transactions(df, 'shinhan', YEAR, month)

    df = parse_payroll_freelance(xl_dash, YEAR, month)
    upsert_payroll(df, YEAR, month, 'freelance')

    df = parse_payroll_insured(xl_dash, YEAR, month)
    upsert_payroll(df, YEAR, month, 'insured')

print('\n=== 저장 현황 ===')
from modules.db import get_conn
conn = get_conn()
for t in ['card_sales','bank_transactions','payroll']:
    cnt = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    print(f'  {t}: {cnt}건')
conn.close()
