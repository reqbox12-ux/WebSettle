import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 하나 탭: 적요(C열=index2) -> 지점(index7), 계정과목(index9) 매핑 추출
df_hana = pd.read_excel('정산내역.xlsx', sheet_name=1, header=0)
print('=== 하나 탭 컬럼명 ===')
print(list(df_hana.columns))
print()

# 제외가 아닌 것만 (실제 분류된 것들)
df_hana_filtered = df_hana[df_hana['계정과목'] != '제외'].copy()
# 적요 -> 지점, 계정과목 매핑
mapping = df_hana_filtered.groupby(['적요', '지점', '계정과목']).size().reset_index(name='count')
mapping = mapping.sort_values('count', ascending=False)
print('=== 하나: 적요 → 지점/계정과목 (상위 40개) ===')
print(mapping.head(40).to_string(index=False))
