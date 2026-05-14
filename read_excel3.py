import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

xl2 = pd.ExcelFile('지점별 대시보드.xlsx')
sheets = xl2.sheet_names
print('=== 지점별 대시보드 시트 목록 ===')
for i, s in enumerate(sheets):
    print(f'  {i}: {s}')

# 첫번째 시트(기본대시보드) 구조 확인
df_dash = pd.read_excel('지점별 대시보드.xlsx', sheet_name=0, header=None, nrows=10)
print()
print('=== 첫번째 탭 구조 ===')
for i, row in df_dash.iterrows():
    vals = [str(v)[:20] if str(v) != 'nan' else '' for v in row]
    vals = [v for v in vals if v]  # 빈값 제거
    if vals:
        print(vals)

# 지점 탭 중 하나 (예: 3번째 탭) 구조 확인
df_branch = pd.read_excel('지점별 대시보드.xlsx', sheet_name=2, header=None, nrows=15)
print()
print(f'=== {sheets[2]} 탭 구조 ===')
for i, row in df_branch.iterrows():
    vals = [str(v)[:20] if str(v) != 'nan' else '' for v in row]
    vals_stripped = [v for v in vals if v]
    if vals_stripped:
        print(vals[:10])
