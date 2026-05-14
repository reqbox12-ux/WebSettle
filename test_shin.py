import pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8')
from modules.parser import parse_shinhan
xl = pd.ExcelFile('정산내역.xlsx')
df = parse_shinhan(xl, 2026, 3)
print('신한 3월 파싱 성공:', len(df), '건')
print('미분류:', df['needs_review'].sum(), '건')
