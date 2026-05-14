import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 지점별 대시보드 탭 A열 계정과목 확인
df = pd.read_excel('지점별 대시보드.xlsx', sheet_name='지점별 대시보드', header=None)
print('=== 지점별 대시보드 탭 A열 전체 ===')
for i, row in df.iterrows():
    v = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
    if v and v != 'nan' and v != 'NaT':
        print(f'  행{i:02d}: {v}')
