import pandas as pd
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

df_hana = pd.read_excel('정산내역.xlsx', sheet_name=1, header=0)
df_shin = pd.read_excel('정산내역.xlsx', sheet_name=2, header=0)

rules = {"hana": [], "shinhan": []}

# 하나: 적요 -> 지점, 계정과목 (제외 제외, 카드매출 제외)
hana_filtered = df_hana[
    (~df_hana['계정과목'].isin(['제외'])) & 
    (df_hana['지점'].notna()) & 
    (df_hana['계정과목'].notna())
].copy()

hana_map = hana_filtered.groupby(['적요','지점','계정과목']).size().reset_index(name='cnt')
hana_map = hana_map.sort_values('cnt', ascending=False)

for _, row in hana_map.iterrows():
    rules['hana'].append({
        "keyword": str(row['적요']),
        "branch": str(row['지점']),
        "category": str(row['계정과목']),
        "count": int(row['cnt'])
    })

# 신한: 내용(G열) -> 지점, 계정과목
shin_filtered = df_shin[
    (~df_shin['계정과목'].isin(['제외'])) &
    (df_shin['지점'].notna()) &
    (df_shin['계정과목'].notna())
].copy()

shin_map = shin_filtered.groupby(['내용','지점','계정과목']).size().reset_index(name='cnt')
shin_map = shin_map.sort_values('cnt', ascending=False)

for _, row in shin_map.iterrows():
    rules['shinhan'].append({
        "keyword": str(row['내용']),
        "branch": str(row['지점']),
        "category": str(row['계정과목']),
        "count": int(row['cnt'])
    })

with open('mapping/keyword_rules.json', 'w', encoding='utf-8') as f:
    json.dump(rules, f, ensure_ascii=False, indent=2)

print(f"하나 규칙: {len(rules['hana'])}개")
print(f"신한 규칙: {len(rules['shinhan'])}개")
