import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 지점별 대시보드 - 개별 지점탭 고정비 구조 파악
# 동수원자이1차 탭 전체 확인
xl2 = pd.ExcelFile('지점별 대시보드.xlsx')
df = pd.read_excel('지점별 대시보드.xlsx', sheet_name=4, header=None)
print(f'=== 동수원자이1차 탭 전체 ({len(df)}행) ===')
for i, row in df.iterrows():
    vals = [str(v)[:25] if str(v) not in ('nan', 'NaT') else '' for v in row]
    vals_stripped = [v for v in vals if v]
    if vals_stripped:
        print(f'행{i:02d}:', vals[:12])
