import pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8')
xl = pd.ExcelFile('정산내역.xlsx')
df = xl.parse(sheet_name=2, header=0)
print('신한 탭 실제 컬럼 수:', len(df.columns))
print('컬럼 목록:')
for i, c in enumerate(df.columns):
    print(f'  {i}: {c}')
print()
print('첫 2행:')
for _, row in df.head(2).iterrows():
    vals = [str(v)[:20] if str(v) not in ('nan','NaT') else '' for v in row]
    print(vals)
