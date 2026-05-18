"""
인증 모듈 — SQLite 기반 사용자 관리 + bcrypt 암호화
기본 관리자: admin / Admin1234!
"""

import bcrypt
from modules.db import get_conn


# ── 테이블 초기화 ─────────────────────────────────────────────

def init_users_table():
    """users 테이블 생성 + 기본 admin 계정 없으면 생성"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            name       TEXT NOT NULL,
            password   TEXT NOT NULL,
            role       TEXT DEFAULT 'user',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.commit()

    # 기본 admin 계정 없으면 생성
    row = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not row:
        pw_hash = bcrypt.hashpw("Admin1234!".encode(), bcrypt.gensalt()).decode()
        c.execute(
            "INSERT INTO users (username, name, password, role) VALUES (?,?,?,?)",
            ("admin", "관리자", pw_hash, "admin")
        )
        conn.commit()
    conn.close()


# ── 로그인 검증 ───────────────────────────────────────────────

def verify_login(username: str, password: str) -> dict | None:
    """
    로그인 성공 시 {"username":..., "name":..., "role":...} 반환
    실패 시 None
    """
    conn = get_conn()
    row = conn.execute(
        "SELECT username, name, password, role FROM users WHERE username=?",
        (username.strip(),)
    ).fetchone()
    conn.close()

    if row and bcrypt.checkpw(password.encode(), row[2].encode()):
        return {"username": row[0], "name": row[1], "role": row[3]}
    return None


# ── 사용자 관리 ───────────────────────────────────────────────

def get_all_users() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, username, name, role, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "name": r[2], "role": r[3], "created_at": r[4]} for r in rows]


def add_user(username: str, name: str, password: str, role: str = "user") -> bool:
    """추가 성공 True, 중복 False"""
    try:
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = get_conn()
        conn.execute(
            "INSERT INTO users (username, name, password, role) VALUES (?,?,?,?)",
            (username.strip(), name.strip(), pw_hash, role)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def delete_user(user_id: int) -> bool:
    try:
        conn = get_conn()
        conn.execute("DELETE FROM users WHERE id=? AND username != 'admin'", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def change_password(username: str, new_password: str) -> bool:
    try:
        pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        conn = get_conn()
        conn.execute("UPDATE users SET password=? WHERE username=?", (pw_hash, username))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
