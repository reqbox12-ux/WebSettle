#!/usr/bin/env python3
"""PostgreSQL 연결 테스트"""
import os
import sys

# .streamlit/secrets.toml에서 환경변수 로드
os.environ["DATABASE_URL"] = "postgresql://postgres:[Fkdhszlwm85]@db.rmqfbwpsmypsbeiefjuk.supabase.co:5432/postgres"

try:
    from modules.db import get_conn, init_db, USE_POSTGRES

    print(f"[OK] PostgreSQL mode: {USE_POSTGRES}")
    print(f"[OK] DATABASE_URL configured")

    # 연결 테스트
    conn = get_conn()
    if conn:
        print(f"[OK] Supabase PostgreSQL connected!")

        # 테이블 초기화
        init_db()
        print(f"[OK] Tables created")

        # 간단한 쿼리 테스트
        c = conn.cursor()
        c.execute("SELECT version()")
        version = c.fetchone()
        print(f"[OK] PostgreSQL version: {version[0][:50]}...")

        conn.close()
        print("\n[SUCCESS] All tests passed!")
    else:
        print("[FAIL] Connection failed")
        sys.exit(1)

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
