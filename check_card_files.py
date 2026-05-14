import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 카드사 결과 집계 조회 1월 - 구조 확인
df1 = pd.read_excel('카드사 결과 집계 조회1월.xlsx', header=None, nrows=5)
print('=== 카드사 결과 집계 조회 구조 (상위5행) ===')
print(f'총 컬럼수: {len(df1.columns)}')
for i, row in df1.iterrows():
    vals = [str(v)[:20] if str(v) not in ('nan','NaT') else '' for v in row]
    print(f'행{i}:', vals)

print()

# 신용카드 1월 - 구조 확인
df2 = pd.read_excel('신용카드1월.xlsx', header=None, nrows=5)
print('=== 신용카드 구조 (상위5행) ===')
print(f'총 컬럼수: {len(df2.columns)}')
for i, row in df2.iterrows():
    vals = [str(v)[:20] if str(v) not in ('nan','NaT') else '' for v in row]
    print(f'행{i}:', vals)
