import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

xl = pd.ExcelFile('정산내역.xlsx')

for idx in range(3):
    df = pd.read_excel('정산내역.xlsx', sheet_name=idx, header=None, nrows=6)
    sheet_name = xl.sheet_names[idx]
    print('=== ' + sheet_name + ' (cols:' + str(len(df.columns)) + ') ===')
    for i, row in df.iterrows():
        vals = [str(v)[:25] if str(v) != 'nan' else '' for v in row]
        print(vals)
    print()
