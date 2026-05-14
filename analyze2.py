import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 신한 탭: G열(내용) -> 지점, 계정과목
df_shin = pd.read_excel('정산내역.xlsx', sheet_name=2, header=0)
print('=== 신한 탭 컬럼명 ===')
print(list(df_shin.columns))
print()

# 내용.1이 실제 사용자 입력 내용열 (G열에 해당)
col_content = '내용'  # G열 = index 6 = '내용'
col_branch = '지점'
col_category = '계정과목'

df_shin_filtered = df_shin[df_shin[col_category] != '제외'].copy()
mapping = df_shin_filtered.groupby([col_content, col_branch, col_category]).size().reset_index(name='count')
mapping = mapping.sort_values('count', ascending=False)
print('=== 신한: 내용(G열) → 지점/계정과목 (상위 40개) ===')
print(mapping.head(40).to_string(index=False))
print()

# 카드정산 탭 지점명 전체
df_card = pd.read_excel('정산내역.xlsx', sheet_name=0, header=None)
print('=== 카드정산 탭 가맹점명(0열) 전체 고유값 ===')
for b in sorted(df_card[0].dropna().unique()):
    print(' ', b)
