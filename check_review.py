import sys
sys.stdout.reconfigure(encoding='utf-8')
from modules.db import get_conn
import pandas as pd
conn = get_conn()
df = pd.read_sql("SELECT year, month, bank, tx_date, description, deposit, withdrawal, branch, category FROM bank_transactions WHERE needs_review=1", conn)
conn.close()
for _, r in df.iterrows():
    print(f'{r.year}년 {r.month}월 [{r.bank}] {r.tx_date} | {r.description} | 입금:{r.deposit} 출금:{r.withdrawal}')
