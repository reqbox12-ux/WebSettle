import sys
sys.stdout.reconfigure(encoding='utf-8')
from modules.db import get_conn
conn = get_conn()
# 기존 규칙에 '중진공대출' 키워드 추가 (본사/이자비용)
conn.execute('''
    INSERT OR IGNORE INTO keyword_rules (bank, keyword, branch, category, hit_count)
    VALUES ('shinhan', '중진공대출', '본사', '이자비용', 3)
''')
# 미분류 건 직접 업데이트
conn.execute('''
    UPDATE bank_transactions 
    SET branch='본사', category='이자비용', needs_review=0
    WHERE needs_review=1 AND description LIKE '%중진공대출%'
''')
conn.commit()
cnt = conn.execute("SELECT COUNT(*) FROM bank_transactions WHERE needs_review=1").fetchone()[0]
print(f'남은 미분류: {cnt}건')
conn.close()
