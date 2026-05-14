import sys
sys.stdout.reconfigure(encoding='utf-8')
from modules.db import init_db, load_keyword_rules
init_db()
load_keyword_rules()
print('DB init OK')

from modules.parser import parse_card_sales, parse_hana, parse_shinhan
import pandas as pd
xl = pd.ExcelFile('정산내역.xlsx')

card = parse_card_sales(xl, 2026, 4)
print('card rows:', len(card))
print(card.head(2).to_string())

hana = parse_hana(xl, 2026, 4)
print('hana rows:', len(hana), ' needs_review:', hana['needs_review'].sum())

shin = parse_shinhan(xl, 2026, 4)
print('shin rows:', len(shin), ' needs_review:', shin['needs_review'].sum())
