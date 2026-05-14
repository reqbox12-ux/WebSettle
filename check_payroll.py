import pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8')
xl = pd.ExcelFile('지점별 대시보드.xlsx')
df = xl.parse('사업소득자', header=None)
print('총 컬럼수:', len(df.columns))
print('헤더행(0):', [str(v) for v in df.iloc[0]])
print('헤더행(1):', [str(v) for v in df.iloc[1]])
# 실 지급액 위치 찾기
row1 = df.iloc[1].tolist()
positions = [i for i, v in enumerate(row1) if '실' in str(v) and '지급' in str(v)]
print('실지급액 컬럼 인덱스(0-based):', positions)
# 알파벳 변환
import string
def idx_to_col(n):
    result = ''
    while n >= 0:
        result = string.ascii_uppercase[n % 26] + result
        n = n // 26 - 1
    return result
print('실지급액 Excel열:', [idx_to_col(i) for i in positions])
