import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

xl2 = pd.ExcelFile('지점별 대시보드.xlsx')

# 사업소득자 탭 전체
df_sa = pd.read_excel('지점별 대시보드.xlsx', sheet_name=0, header=None)
print(f'=== 사업소득자 탭 ({len(df_sa)}행 x {len(df_sa.columns)}열) ===')
for i, row in df_sa.iterrows():
    vals = [str(v)[:22] if str(v) not in ('nan','NaT') else '' for v in row]
    vals_stripped = [v for v in vals if v]
    if vals_stripped:
        print(f'행{i:02d}:', vals[:14])
