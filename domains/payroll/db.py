"""
domains/payroll/db.py — 급여 도메인 전용 DB 테이블 초기화 및 쿼리
"""
import sqlite3
from shared.db import get_conn


def _migrate_employees_emp_type(conn):
    """기존 employees 테이블의 emp_type 제약을 business/tax_exempt 포함으로 마이그레이션"""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='employees'"
    ).fetchone()
    if not row or "'business'" in row[0]:
        return
    conn.executescript("""
        ALTER TABLE employees RENAME TO _employees_old;
        CREATE TABLE employees (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            branch          TEXT NOT NULL,
            emp_type        TEXT NOT NULL CHECK(emp_type IN ('insured','freelance','business','tax_exempt')),
            dependents      INTEGER DEFAULT 1,
            base_salary     INTEGER DEFAULT 0,
            meal_allowance  INTEGER DEFAULT 0,
            transport       INTEGER DEFAULT 0,
            email           TEXT DEFAULT '',
            id_number       TEXT DEFAULT '',
            join_date       TEXT DEFAULT '',
            is_active       INTEGER DEFAULT 1,
            note            TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        INSERT INTO employees SELECT * FROM _employees_old;
        DROP TABLE _employees_old;
    """)
    conn.commit()


def init_payroll_tables():
    """급여 시스템 전용 테이블 생성"""
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        -- 직원 마스터
        CREATE TABLE IF NOT EXISTS employees (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            branch          TEXT NOT NULL,
            emp_type        TEXT NOT NULL CHECK(emp_type IN ('insured','freelance','business','tax_exempt')),
            dependents      INTEGER DEFAULT 1,
            base_salary     INTEGER DEFAULT 0,
            meal_allowance  INTEGER DEFAULT 0,
            transport       INTEGER DEFAULT 0,
            email           TEXT DEFAULT '',
            id_number       TEXT DEFAULT '',
            join_date       TEXT DEFAULT '',
            is_active       INTEGER DEFAULT 1,
            note            TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 급여 계산 항목 (월별 직원별)
        CREATE TABLE IF NOT EXISTS payroll_entries (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            year                INTEGER NOT NULL,
            month               INTEGER NOT NULL,
            employee_id         INTEGER NOT NULL,
            branch              TEXT NOT NULL,
            emp_type            TEXT NOT NULL,
            gross_pay           INTEGER DEFAULT 0,
            meal_allowance      INTEGER DEFAULT 0,
            transport           INTEGER DEFAULT 0,
            taxable_base        INTEGER DEFAULT 0,
            income_tax          INTEGER DEFAULT 0,
            local_tax           INTEGER DEFAULT 0,
            pension_emp         INTEGER DEFAULT 0,
            health_emp          INTEGER DEFAULT 0,
            employ_emp          INTEGER DEFAULT 0,
            total_deduction     INTEGER DEFAULT 0,
            net_pay             INTEGER DEFAULT 0,
            company_pension     INTEGER DEFAULT 0,
            company_health      INTEGER DEFAULT 0,
            company_employ      INTEGER DEFAULT 0,
            company_accident    INTEGER DEFAULT 0,
            status              TEXT DEFAULT 'draft',
            note                TEXT DEFAULT '',
            created_at          TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(year, month, employee_id)
        );

        -- 간이세액표 (국세청)
        CREATE TABLE IF NOT EXISTS tax_brackets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            salary_from     INTEGER NOT NULL,
            salary_to       INTEGER NOT NULL,
            dependents_0    INTEGER DEFAULT 0,
            dependents_1    INTEGER DEFAULT 0,
            dependents_2    INTEGER DEFAULT 0,
            dependents_3    INTEGER DEFAULT 0,
            dependents_4    INTEGER DEFAULT 0,
            dependents_5    INTEGER DEFAULT 0,
            dependents_6    INTEGER DEFAULT 0,
            dependents_7    INTEGER DEFAULT 0,
            tax_year        INTEGER DEFAULT 2025
        );

        -- 4대보험 요율 설정
        CREATE TABLE IF NOT EXISTS insurance_rates (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            year            INTEGER NOT NULL UNIQUE,
            pension_rate    REAL DEFAULT 0.045,
            health_rate     REAL DEFAULT 0.03545,
            employ_rate_emp REAL DEFAULT 0.009,
            employ_rate_co  REAL DEFAULT 0.009,
            accident_rate   REAL DEFAULT 0.007,
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 급여 확정 잠금
        CREATE TABLE IF NOT EXISTS payroll_locks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            year        INTEGER NOT NULL,
            month       INTEGER NOT NULL,
            locked_by   TEXT NOT NULL,
            locked_at   TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(year, month)
        );

        -- 4대보험 실납부 고지액 (공단 고지서 기준)
        CREATE TABLE IF NOT EXISTS insurance_actuals (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            year          INTEGER NOT NULL,
            month         INTEGER NOT NULL,
            employee_name TEXT NOT NULL,
            employee_id   INTEGER DEFAULT NULL,
            pension_base  INTEGER DEFAULT 0,
            pension_emp   INTEGER DEFAULT 0,
            pension_co    INTEGER DEFAULT 0,
            health_base   INTEGER DEFAULT 0,
            health_emp    INTEGER DEFAULT 0,
            health_co     INTEGER DEFAULT 0,
            employ_base   INTEGER DEFAULT 0,
            employ_emp    INTEGER DEFAULT 0,
            employ_co     INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(year, month, employee_name)
        );

        -- 이메일 발송 이력
        CREATE TABLE IF NOT EXISTS email_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            year            INTEGER NOT NULL,
            month           INTEGER NOT NULL,
            employee_id     INTEGER NOT NULL,
            recipient_email TEXT NOT NULL,
            subject         TEXT,
            status          TEXT DEFAULT 'pending',
            sent_at         TEXT,
            error_msg       TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    _migrate_employees_emp_type(conn)

    # 기본 4대보험 요율 (2025년)
    exists = conn.execute("SELECT id FROM insurance_rates WHERE year=2025").fetchone()
    if not exists:
        conn.execute("""
            INSERT INTO insurance_rates
            (year, pension_rate, health_rate, employ_rate_emp, employ_rate_co, accident_rate)
            VALUES (2025, 0.045, 0.03545, 0.009, 0.009, 0.007)
        """)
        conn.commit()

    conn.close()


# ── 직원 마스터 쿼리 ─────────────────────────────────────────
def get_all_employees(active_only: bool = True) -> list[dict]:
    conn = get_conn()
    q = "SELECT * FROM employees"
    if active_only:
        q += " WHERE is_active=1"
    q += " ORDER BY branch, emp_type, name"
    cur  = conn.execute(q)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def get_employees_by_branch(branch: str, active_only: bool = True) -> list[dict]:
    conn = get_conn()
    q    = "SELECT * FROM employees WHERE branch=?"
    params: list = [branch]
    if active_only:
        q += " AND is_active=1"
    q += " ORDER BY emp_type, name"
    cur  = conn.execute(q, params)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def upsert_employee(data: dict) -> int:
    """직원 추가/수정. 반환값: employee_id"""
    conn = get_conn()
    if data.get("id"):
        conn.execute("""
            UPDATE employees SET
                name=?, branch=?, emp_type=?, dependents=?,
                base_salary=?, meal_allowance=?, transport=?,
                email=?, id_number=?, join_date=?, is_active=?, note=?
            WHERE id=?
        """, (
            data["name"], data["branch"], data["emp_type"], data.get("dependents", 1),
            data.get("base_salary", 0), data.get("meal_allowance", 0), data.get("transport", 0),
            data.get("email", ""), data.get("id_number", ""), data.get("join_date", ""),
            data.get("is_active", 1), data.get("note", ""),
            data["id"],
        ))
        emp_id = data["id"]
    else:
        cur = conn.execute("""
            INSERT INTO employees
            (name, branch, emp_type, dependents, base_salary, meal_allowance,
             transport, email, id_number, join_date, is_active, note)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["name"], data["branch"], data["emp_type"], data.get("dependents", 1),
            data.get("base_salary", 0), data.get("meal_allowance", 0), data.get("transport", 0),
            data.get("email", ""), data.get("id_number", ""), data.get("join_date", ""),
            data.get("is_active", 1), data.get("note", ""),
        ))
        emp_id = cur.lastrowid
    conn.commit()
    conn.close()
    return emp_id


def delete_employee(employee_id: int) -> bool:
    """직원 비활성화 (소프트 삭제)"""
    try:
        conn = get_conn()
        conn.execute("UPDATE employees SET is_active=0 WHERE id=?", (employee_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ── 급여 계산 항목 쿼리 ───────────────────────────────────────
def get_payroll_entries(year: int, month: int, branch: str = None) -> list[dict]:
    conn = get_conn()
    q    = """
        SELECT pe.*, e.name, e.email, e.id_number, e.join_date
        FROM payroll_entries pe
        JOIN employees e ON pe.employee_id = e.id
        WHERE pe.year=? AND pe.month=?
    """
    params: list = [year, month]
    if branch:
        q += " AND pe.branch=?"
        params.append(branch)
    q += " ORDER BY pe.branch, e.emp_type, e.name"
    cur  = conn.execute(q, params)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def save_payroll_entry(entry: dict) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO payroll_entries
            (year, month, employee_id, branch, emp_type,
             gross_pay, meal_allowance, transport, taxable_base,
             income_tax, local_tax, pension_emp, health_emp, employ_emp,
             total_deduction, net_pay,
             company_pension, company_health, company_employ, company_accident,
             status, note)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            entry["year"], entry["month"], entry["employee_id"],
            entry["branch"], entry["emp_type"],
            entry.get("gross_pay", 0), entry.get("meal_allowance", 0), entry.get("transport", 0),
            entry.get("taxable_base", 0),
            entry.get("income_tax", 0), entry.get("local_tax", 0),
            entry.get("pension_emp", 0), entry.get("health_emp", 0), entry.get("employ_emp", 0),
            entry.get("total_deduction", 0), entry.get("net_pay", 0),
            entry.get("company_pension", 0), entry.get("company_health", 0),
            entry.get("company_employ", 0), entry.get("company_accident", 0),
            entry.get("status", "draft"), entry.get("note", ""),
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[payroll_entry save] {e}")
        return False


# ── 4대보험 요율 쿼리 ─────────────────────────────────────────
def get_insurance_rates(year: int = 2025) -> dict:
    conn = get_conn()
    row  = conn.execute("SELECT * FROM insurance_rates WHERE year=?", (year,)).fetchone()
    conn.close()
    if row:
        return {
            "year": row[1], "pension_rate": row[2], "health_rate": row[3],
            "employ_rate_emp": row[4], "employ_rate_co": row[5], "accident_rate": row[6],
        }
    return {
        "year": year, "pension_rate": 0.045, "health_rate": 0.03545,
        "employ_rate_emp": 0.009, "employ_rate_co": 0.009, "accident_rate": 0.007,
    }


def save_insurance_rates(data: dict) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO insurance_rates
            (year, pension_rate, health_rate, employ_rate_emp, employ_rate_co, accident_rate)
            VALUES (?,?,?,?,?,?)
        """, (
            data["year"], data["pension_rate"], data["health_rate"],
            data["employ_rate_emp"], data["employ_rate_co"], data["accident_rate"],
        ))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ── 간이세액표 쿼리 ───────────────────────────────────────────
def get_tax_brackets(tax_year: int = 2025) -> list[dict]:
    conn = get_conn()
    cur  = conn.execute("SELECT * FROM tax_brackets WHERE tax_year=? ORDER BY salary_from",
                        (tax_year,))
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def upsert_tax_brackets(rows: list[dict], tax_year: int = 2025) -> bool:
    """간이세액표 전체 교체"""
    try:
        conn = get_conn()
        conn.execute("DELETE FROM tax_brackets WHERE tax_year=?", (tax_year,))
        for r in rows:
            conn.execute("""
                INSERT INTO tax_brackets
                (salary_from, salary_to,
                 dependents_0, dependents_1, dependents_2, dependents_3,
                 dependents_4, dependents_5, dependents_6, dependents_7, tax_year)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                r["salary_from"], r["salary_to"],
                r.get("dependents_0", 0), r.get("dependents_1", 0),
                r.get("dependents_2", 0), r.get("dependents_3", 0),
                r.get("dependents_4", 0), r.get("dependents_5", 0),
                r.get("dependents_6", 0), r.get("dependents_7", 0),
                tax_year,
            ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[tax_brackets upsert] {e}")
        return False


# ── 급여 잠금 ────────────────────────────────────────────────
def lock_payroll(year: int, month: int, username: str) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            INSERT OR IGNORE INTO payroll_locks (year, month, locked_by)
            VALUES (?,?,?)
        """, (year, month, username))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def unlock_payroll(year: int, month: int) -> bool:
    try:
        conn = get_conn()
        conn.execute("DELETE FROM payroll_locks WHERE year=? AND month=?", (year, month))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def is_payroll_locked(year: int, month: int) -> bool:
    conn = get_conn()
    row  = conn.execute("SELECT id FROM payroll_locks WHERE year=? AND month=?", (year, month)).fetchone()
    conn.close()
    return row is not None


# ── 4대보험 실납부 ───────────────────────────────────────────
def save_insurance_actuals(year: int, month: int, records: list[dict]) -> tuple[int, int]:
    """공단 고지내역 저장. 반환: (저장 수, 미매칭 수)"""
    conn      = get_conn()
    saved     = 0
    unmatched = 0
    for rec in records:
        name   = rec.get("employee_name", "").strip()
        if not name:
            continue
        emp_row = conn.execute(
            "SELECT id FROM employees WHERE name=? AND is_active=1", (name,)
        ).fetchone()
        emp_id = emp_row[0] if emp_row else None
        if not emp_id:
            unmatched += 1
        conn.execute("""
            INSERT OR REPLACE INTO insurance_actuals
            (year, month, employee_name, employee_id,
             pension_base, pension_emp, pension_co,
             health_base, health_emp, health_co,
             employ_base, employ_emp, employ_co)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            year, month, name, emp_id,
            rec.get("pension_base", 0), rec.get("pension_emp", 0), rec.get("pension_co", 0),
            rec.get("health_base", 0), rec.get("health_emp", 0), rec.get("health_co", 0),
            rec.get("employ_base", 0), rec.get("employ_emp", 0), rec.get("employ_co", 0),
        ))
        saved += 1
    conn.commit()
    conn.close()
    return saved, unmatched


def get_insurance_actual(year: int, month: int, employee_id: int) -> dict | None:
    conn = get_conn()
    cur  = conn.execute(
        "SELECT * FROM insurance_actuals WHERE year=? AND month=? AND employee_id=?",
        (year, month, employee_id),
    )
    cols = [d[0] for d in cur.description]
    row  = cur.fetchone()
    conn.close()
    return dict(zip(cols, row)) if row else None


def get_all_insurance_actuals(year: int, month: int) -> list[dict]:
    conn = get_conn()
    cur  = conn.execute(
        "SELECT * FROM insurance_actuals WHERE year=? AND month=? ORDER BY employee_name",
        (year, month),
    )
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def delete_insurance_actuals(year: int, month: int) -> bool:
    try:
        conn = get_conn()
        conn.execute("DELETE FROM insurance_actuals WHERE year=? AND month=?", (year, month))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ── 이메일 로그 ──────────────────────────────────────────────
def log_email(year: int, month: int, employee_id: int,
              email: str, subject: str, status: str, error: str = "") -> bool:
    try:
        import time
        conn = get_conn()
        conn.execute("""
            INSERT INTO email_logs
            (year, month, employee_id, recipient_email, subject, status, sent_at, error_msg)
            VALUES (?,?,?,?,?,?,?,?)
        """, (year, month, employee_id, email, subject, status,
              time.strftime("%Y-%m-%d %H:%M:%S") if status == "sent" else None, error))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
