import pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8')
from modules.parser import parse_payroll_freelance
xl = pd.ExcelFile('지점별 대시보드.xlsx')
for m in [1,2,3,4]:
    df = parse_payroll_freelance(xl, 2026, m)
    r = df[df['branch']=='라온골프 서초'].iloc[0] if len(df[df['branch']=='라온골프 서초']) > 0 else None
    if r is not None:
        print(f'{m}월 라온골프서초: gross={r.gross_pay:,} net={r.net_pay:,}')
