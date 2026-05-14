import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 지점별집계 탭 확인
df = pd.read_excel('지점별 대시보드.xlsx', sheet_name=1, header=None, nrows=30)
print('=== 지점별집계 탭 ===')
for i, row in df.iterrows():
    vals = [str(v)[:20] if str(v) != 'nan' else '' for v in row]
    vals_stripped = [v for v in vals if v]
    if vals_stripped:
        print(vals[:12])

print()

# 개별 지점탭 (동수원자이1차) 확인
df2 = pd.read_excel('지점별 대시보드.xlsx', sheet_name=4, header=None, nrows=35)
sheets = pd.ExcelFile('지점별 대시보드.xlsx').sheet_names
print(f'=== {sheets[4]} 탭 (상세) ===')
for i, row in df2.iterrows():
    vals = [str(v)[:20] if str(v) != 'nan' else '' for v in row]
    vals_stripped = [v for v in vals if v]
    if vals_stripped:
        print(vals[:10])
