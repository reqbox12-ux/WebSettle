import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 지점별집계 탭 전체
df_jj = pd.read_excel('지점별 대시보드.xlsx', sheet_name=1, header=None)
print(f'=== 지점별집계 탭 ({len(df_jj)}행 x {len(df_jj.columns)}열) ===')
for i, row in df_jj.iterrows():
    vals = [str(v)[:20] if str(v) not in ('nan','NaT') else '' for v in row]
    vals_stripped = [v for v in vals if v]
    if vals_stripped:
        print(f'행{i:02d}:', vals[:16])
