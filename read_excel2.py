import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 하나 탭 - 지점 고유값
df_hana = pd.read_excel('정산내역.xlsx', sheet_name=1, header=0)
print('=== 하나 탭 컬럼 ===')
print(list(df_hana.columns))
print('지점 고유값:', df_hana.iloc[:,7].dropna().unique().tolist() if len(df_hana.columns) > 7 else 'N/A')
print('계정과목 고유값:', df_hana.iloc[:,9].dropna().unique().tolist() if len(df_hana.columns) > 9 else 'N/A')
print('총 행수:', len(df_hana))
print()

# 신한 탭
df_shin = pd.read_excel('정산내역.xlsx', sheet_name=2, header=0)
print('=== 신한 탭 컬럼 ===')
print(list(df_shin.columns))
print('지점 고유값:', df_shin.iloc[:,12].dropna().unique().tolist() if len(df_shin.columns) > 12 else 'N/A')
print('계정과목 고유값:', df_shin.iloc[:,14].dropna().unique().tolist() if len(df_shin.columns) > 14 else 'N/A')
print('총 행수:', len(df_shin))
print()

# 카드정산 탭
df_card = pd.read_excel('정산내역.xlsx', sheet_name=0, header=None)
print('=== 카드정산 탭 ===')
print('총 행수:', len(df_card))
# 지점명 추출 (0열에서 '라온스포츠' 이후)
branches = df_card[0].dropna().unique()
print('지점 예시 (0열 고유값 일부):')
for b in branches[:10]:
    print(' ', b)
