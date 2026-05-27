"""
branch_server.py — 라온스포츠 지점 포털 FastAPI 서버
Port: 8502  |  Auth: JWT (8h)  |  DB: data/settlement.db (shared with ERP)
"""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import bcrypt
from fastapi import (
    Depends, FastAPI, File, Form, HTTPException, Request, UploadFile,
    status,
)
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from pydantic import BaseModel

# ── Domain imports ─────────────────────────────────────────────────────────────
from domains.branch_app.db import (
    init_branch_tables,
    get_announcements, create_announcement,
    get_as_requests, create_as_request, update_as_status,
    get_supply_requests, create_supply_request, update_supply_status,
    get_inventory, upsert_inventory_item, adjust_inventory,
    get_members, get_member, upsert_member,
    get_member_memberships, create_membership,
    get_class_schedules, upsert_class_schedule,
)
from domains.payroll.db import (
    init_payroll_tables,
    attendance_clock_in, attendance_clock_out,
    get_attendance_record, get_monthly_attendance,
    get_payroll_entries,
    verify_employee_login,
)
from shared.db import get_conn

# ── JWT Config ─────────────────────────────────────────────────────────────────
SECRET_KEY = "RAON_BRANCH_SECRET_2026"
ALGORITHM  = "HS256"
TOKEN_EXPIRE_HOURS = 8

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
STATIC_DIR   = BASE_DIR / "static"
UPLOAD_DIR   = STATIC_DIR / "uploads"
TEMPLATE_DIR = BASE_DIR / "templates"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="라온스포츠 지점 포털", version="3.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


# ── Startup ────────────────────────────────────────────────────────────────────
def init_all_tables():
    """Initialize all required tables on startup."""
    init_payroll_tables()   # includes employee_accounts, attendance, employees
    init_branch_tables()    # includes members, inventory, announcements, etc.
    _init_events_tables()   # events, event_comments, instructors


def _init_events_tables():
    """Create events, event_comments, instructors tables."""
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS events (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        branch      TEXT NOT NULL,
        title       TEXT NOT NULL,
        sub         TEXT DEFAULT '',
        eyebrow     TEXT DEFAULT '',
        content     TEXT DEFAULT '',
        image_path  TEXT DEFAULT '',
        ends_at     TEXT DEFAULT '',
        is_active   INTEGER DEFAULT 1,
        created_by  TEXT DEFAULT '',
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS event_comments (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id   INTEGER NOT NULL,
        author     TEXT NOT NULL,
        content    TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS instructors (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        branch       TEXT NOT NULL,
        name         TEXT NOT NULL,
        english      TEXT DEFAULT '',
        role         TEXT DEFAULT '',
        bio          TEXT DEFAULT '',
        tags         TEXT DEFAULT '[]',
        classes      TEXT DEFAULT '[]',
        curriculum   TEXT DEFAULT '',
        photo_path   TEXT DEFAULT '',
        is_active    INTEGER DEFAULT 1,
        created_at   TEXT DEFAULT (datetime('now','localtime'))
    );
    """)
    conn.commit()
    conn.close()


@app.on_event("startup")
async def on_startup():
    init_all_tables()


# ── Helpers ────────────────────────────────────────────────────────────────────
def _rows(cur) -> list[dict]:
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _one(cur) -> dict | None:
    cols = [d[0] for d in cur.description]
    row  = cur.fetchone()
    return dict(zip(cols, row)) if row else None


def verify_password(plain: str, hashed: str) -> bool:
    """Support both bcrypt and sha256 hashes."""
    if not plain or not hashed:
        return False
    # Detect bcrypt (starts with $2b$ or $2a$)
    h = hashed.encode() if isinstance(hashed, str) else hashed
    if h.startswith(b"$2"):
        try:
            return bcrypt.checkpw(plain.encode(), h)
        except Exception:
            return False
    # Fallback: sha256 (used by existing employee accounts)
    return hashlib.sha256(plain.strip().encode("utf-8")).hexdigest() == hashed


def create_token(payload: dict) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({**payload, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"토큰이 유효하지 않습니다: {e}")


def get_token_from_request(request: Request) -> Optional[str]:
    """Extract bearer token from Authorization header or cookie."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return request.cookies.get("raon_token")


def require_auth(request: Request) -> dict:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    return decode_token(token)


def require_staff(request: Request) -> dict:
    user = require_auth(request)
    if user.get("role") != "staff":
        raise HTTPException(status_code=403, detail="직원 전용 기능입니다")
    return user


def save_upload(file: UploadFile) -> str:
    """Save uploaded file to static/uploads/ and return URL path."""
    ext  = Path(file.filename).suffix if file.filename else ""
    name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / name
    with open(dest, "wb") as f:
        f.write(file.file.read())
    return f"/static/uploads/{name}"


# ── Page Routes ────────────────────────────────────────────────────────────────
@app.get("/")
async def root(request: Request):
    token = get_token_from_request(request)
    if not token:
        return RedirectResponse("/login")
    try:
        decode_token(token)
        return RedirectResponse("/home")
    except HTTPException:
        return RedirectResponse("/login")


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/home")
async def home_page(request: Request):
    return templates.TemplateResponse("app.html", {"request": request, "page": "home"})


@app.get("/attendance")
async def attendance_page(request: Request):
    return templates.TemplateResponse("app.html", {"request": request, "page": "attendance"})


@app.get("/operations")
async def operations_page(request: Request):
    return templates.TemplateResponse("app.html", {"request": request, "page": "operations"})


@app.get("/members")
async def members_page(request: Request):
    return templates.TemplateResponse("app.html", {"request": request, "page": "members"})


@app.get("/classes")
async def classes_page(request: Request):
    return templates.TemplateResponse("app.html", {"request": request, "page": "classes"})


@app.get("/instructors")
async def instructors_page(request: Request):
    return templates.TemplateResponse("app.html", {"request": request, "page": "instructors"})


# ── Auth API ───────────────────────────────────────────────────────────────────
class LoginBody(BaseModel):
    role:       str   # "staff" | "member"
    identifier: str
    password:   str


@app.post("/api/auth/login")
async def api_login(body: LoginBody):
    if body.role == "staff":
        # Use existing verify_employee_login from payroll domain (sha256-based)
        emp = verify_employee_login(body.identifier, body.password)
        if not emp:
            raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다")
        token = create_token({
            "sub":           str(emp["employee_id"]),
            "role":          "staff",
            "name":          emp["name"],
            "branch":        emp.get("branch", ""),
            "must_change_pw": emp.get("must_change_pw", False),
        })
        return {
            "token":         token,
            "role":          "staff",
            "name":          emp["name"],
            "branch":        emp.get("branch", ""),
            "must_change_pw": emp.get("must_change_pw", False),
        }

    elif body.role == "member":
        conn = get_conn()
        # Match by phone (last 4 = PIN) or email
        identifier = body.identifier.strip()
        member = _one(conn.execute(
            "SELECT * FROM members WHERE (phone=? OR email=?) AND status='active' LIMIT 1",
            (identifier, identifier)
        ))
        conn.close()
        if not member:
            raise HTTPException(status_code=401, detail="회원 정보를 찾을 수 없습니다")
        # PIN check: stored as last 4 digits of phone, or pin column
        pin = str(member.get("pin", ""))
        if not pin or not verify_password(body.password, pin) and body.password != pin:
            raise HTTPException(status_code=401, detail="비밀번호(PIN)가 올바르지 않습니다")
        token = create_token({
            "sub":    str(member["id"]),
            "role":   "member",
            "name":   member["name"],
            "branch": member.get("branch", ""),
        })
        return {
            "token":  token,
            "role":   "member",
            "name":   member["name"],
            "branch": member.get("branch", ""),
            "must_change_pw": False,
        }

    raise HTTPException(status_code=400, detail="role은 'staff' 또는 'member'여야 합니다")


@app.post("/api/auth/logout")
async def api_logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie("raon_token")
    return response


@app.get("/api/auth/me")
async def api_me(request: Request):
    user = require_auth(request)
    return {
        "id":     user.get("sub"),
        "role":   user.get("role"),
        "name":   user.get("name"),
        "branch": user.get("branch"),
    }


# ── Home API ───────────────────────────────────────────────────────────────────
@app.get("/api/home/data")
async def api_home_data(request: Request):
    user = require_auth(request)
    branch = user.get("branch", "")
    conn = get_conn()

    anns_cur = conn.execute("""
        SELECT * FROM announcements
        WHERE (target_branch='all' OR target_branch=?)
          AND (expires_at IS NULL OR expires_at >= date('now'))
        ORDER BY priority DESC, created_at DESC LIMIT 3
    """, (branch,))
    announcements = _rows(anns_cur)

    events_cur = conn.execute("""
        SELECT * FROM events
        WHERE (branch=? OR branch='all') AND is_active=1
          AND (ends_at='' OR ends_at >= date('now'))
        ORDER BY created_at DESC LIMIT 3
    """, (branch,))
    events = _rows(events_cur)

    classes_cur = conn.execute("""
        SELECT * FROM class_schedules
        WHERE branch=? AND is_active=1
        ORDER BY start_time LIMIT 4
    """, (branch,))
    classes = _rows(classes_cur)

    conn.close()
    return {"announcements": announcements, "events": events, "classes": classes}


@app.get("/api/home/announcements")
async def api_home_announcements(request: Request):
    user = require_auth(request)
    branch = user.get("branch", "")
    anns = get_announcements(branch)
    return anns


# ── Attendance API ─────────────────────────────────────────────────────────────
@app.get("/api/attendance/today")
async def api_attendance_today(request: Request):
    user = require_staff(request)
    today = datetime.now().strftime("%Y-%m-%d")
    rec   = get_attendance_record(int(user["sub"]), today)
    return rec or {"clock_in": None, "clock_out": None, "status": None, "work_minutes": 0}


class ClockBody(BaseModel):
    time: Optional[str] = None  # HH:MM, defaults to now


@app.post("/api/attendance/clock-in")
async def api_clock_in(request: Request, body: ClockBody):
    user  = require_staff(request)
    emp_id = int(user["sub"])
    today  = datetime.now().strftime("%Y-%m-%d")
    now_t  = body.time or datetime.now().strftime("%H:%M")
    ok, msg = attendance_clock_in(emp_id, today, now_t)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "time": now_t}


@app.post("/api/attendance/clock-out")
async def api_clock_out(request: Request, body: ClockBody):
    user   = require_staff(request)
    emp_id = int(user["sub"])
    today  = datetime.now().strftime("%Y-%m-%d")
    now_t  = body.time or datetime.now().strftime("%H:%M")
    # Get work_start from employees table
    conn = get_conn()
    emp_row = conn.execute(
        "SELECT work_start FROM employees WHERE id=?", (emp_id,)
    ).fetchone()
    conn.close()
    work_start = emp_row[0] if emp_row and emp_row[0] else "09:00"
    ok, msg = attendance_clock_out(emp_id, today, now_t, work_start)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "time": now_t}


@app.get("/api/attendance/monthly")
async def api_attendance_monthly(request: Request, year: int = None, month: int = None):
    user   = require_staff(request)
    emp_id = int(user["sub"])
    now    = datetime.now()
    year   = year  or now.year
    month  = month or now.month
    records = get_monthly_attendance(emp_id, year, month)
    return records


@app.get("/api/attendance/class-schedule")
async def api_attendance_class_schedule(request: Request, year: int = None, month: int = None):
    user   = require_staff(request)
    emp_id = int(user["sub"])
    now    = datetime.now()
    year   = year  or now.year
    month  = month or now.month
    entries = get_payroll_entries(year, month)
    # Filter to current employee
    my_entries = [e for e in entries if e.get("employee_id") == emp_id]
    return my_entries


# ── Operations: Inventory ──────────────────────────────────────────────────────
@app.get("/api/operations/inventory")
async def api_inventory_get(request: Request, branch: str = ""):
    require_staff(request)
    return get_inventory(branch)


class InventoryItem(BaseModel):
    branch:       str
    item_name:    str
    category:     str = "일반"
    quantity:     int = 0
    min_quantity: int = 0
    unit:         str = "개"
    note:         str = ""


@app.post("/api/operations/inventory")
async def api_inventory_add(request: Request, body: InventoryItem):
    require_staff(request)
    rid = upsert_inventory_item(body.dict())
    return {"id": rid}


class AdjustBody(BaseModel):
    type: str  # "in" | "out"
    qty:  int
    note: str = ""


@app.post("/api/operations/inventory/{item_id}/adjust")
async def api_inventory_adjust(request: Request, item_id: int, body: AdjustBody):
    user = require_staff(request)
    adjust_inventory(item_id, body.type, body.qty, user.get("name", ""), body.note)
    return {"ok": True}


# ── Operations: Supply Requests ────────────────────────────────────────────────
@app.get("/api/operations/supply")
async def api_supply_get(request: Request, branch: str = ""):
    require_staff(request)
    return get_supply_requests(branch)


class SupplyBody(BaseModel):
    branch:       str
    item_name:    str
    quantity:     int = 1
    unit:         str = "개"
    reason:       str = ""
    created_name: str = ""


@app.post("/api/operations/supply")
async def api_supply_create(request: Request, body: SupplyBody):
    user = require_staff(request)
    data = body.dict()
    data["created_by"] = int(user["sub"])
    rid = create_supply_request(data)
    return {"id": rid}


class SupplyPatchBody(BaseModel):
    status:        str
    approved_by:   str = ""
    reject_reason: str = ""
    deliver_date:  str = ""


@app.patch("/api/operations/supply/{req_id}")
async def api_supply_patch(request: Request, req_id: int, body: SupplyPatchBody):
    require_staff(request)
    update_supply_status(req_id, body.status, body.approved_by, body.reject_reason, body.deliver_date)
    return {"ok": True}


# ── Operations: A/S ───────────────────────────────────────────────────────────
@app.get("/api/operations/as")
async def api_as_get(request: Request, branch: str = ""):
    require_staff(request)
    return get_as_requests(branch)


class AsBody(BaseModel):
    branch:       str
    title:        str
    description:  str = ""
    priority:     str = "normal"
    created_name: str = ""


@app.post("/api/operations/as")
async def api_as_create(request: Request, body: AsBody):
    user = require_staff(request)
    data = body.dict()
    data["created_by"] = int(user["sub"])
    rid = create_as_request(data)
    return {"id": rid}


class AsPatchBody(BaseModel):
    status:      str
    assigned_to: str = ""
    note:        str = ""


@app.patch("/api/operations/as/{req_id}")
async def api_as_patch(request: Request, req_id: int, body: AsPatchBody):
    require_staff(request)
    update_as_status(req_id, body.status, body.assigned_to, body.note)
    return {"ok": True}


# ── Operations: Events ────────────────────────────────────────────────────────
@app.get("/api/operations/events")
async def api_events_get(request: Request, branch: str = ""):
    require_auth(request)
    conn = get_conn()
    cur  = conn.execute(
        "SELECT * FROM events WHERE (branch=? OR branch='all') ORDER BY created_at DESC",
        (branch,)
    )
    rows = _rows(cur)
    conn.close()
    return rows


@app.post("/api/operations/events")
async def api_events_create(
    request: Request,
    branch:  str        = Form(""),
    title:   str        = Form(...),
    content: str        = Form(""),
    eyebrow: str        = Form(""),
    ends_at: str        = Form(""),
    image:   UploadFile = File(None),
):
    user = require_staff(request)
    image_path = save_upload(image) if image and image.filename else ""
    conn = get_conn()
    cur  = conn.execute(
        """INSERT INTO events (branch, title, content, eyebrow, ends_at, image_path, created_by)
           VALUES (?,?,?,?,?,?,?)""",
        (branch or user.get("branch", ""), title, content, eyebrow, ends_at,
         image_path, user.get("name", ""))
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return {"id": rid}


@app.get("/api/operations/events/{event_id}")
async def api_events_detail(request: Request, event_id: int):
    require_auth(request)
    conn = get_conn()
    ev   = _one(conn.execute("SELECT * FROM events WHERE id=?", (event_id,)))
    if not ev:
        conn.close()
        raise HTTPException(status_code=404, detail="이벤트를 찾을 수 없습니다")
    comments = _rows(conn.execute(
        "SELECT * FROM event_comments WHERE event_id=? ORDER BY created_at", (event_id,)
    ))
    conn.close()
    return {**ev, "comments": comments}


class EventPatchBody(BaseModel):
    title:     Optional[str] = None
    content:   Optional[str] = None
    eyebrow:   Optional[str] = None
    ends_at:   Optional[str] = None
    is_active: Optional[int] = None


@app.patch("/api/operations/events/{event_id}")
async def api_events_patch(request: Request, event_id: int, body: EventPatchBody):
    require_staff(request)
    updates = {k: v for k, v in body.dict().items() if v is not None}
    if not updates:
        return {"ok": True}
    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn = get_conn()
    conn.execute(f"UPDATE events SET {set_clause} WHERE id=?", (*updates.values(), event_id))
    conn.commit()
    conn.close()
    return {"ok": True}


class CommentBody(BaseModel):
    content: str


@app.post("/api/operations/events/{event_id}/comment")
async def api_events_comment(request: Request, event_id: int, body: CommentBody):
    user = require_auth(request)
    conn = get_conn()
    conn.execute(
        "INSERT INTO event_comments (event_id, author, content) VALUES (?,?,?)",
        (event_id, user.get("name", ""), body.content)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


# ── Operations: Announcements ─────────────────────────────────────────────────
@app.get("/api/operations/announcements")
async def api_announcements_get(request: Request, branch: str = ""):
    require_auth(request)
    return get_announcements(branch)


class AnnouncementBody(BaseModel):
    title:         str
    content:       str = ""
    priority:      str = "normal"
    target_branch: str = "all"
    created_by:    str = ""
    expires_at:    Optional[str] = None


@app.post("/api/operations/announcements")
async def api_announcements_create(request: Request, body: AnnouncementBody):
    user = require_staff(request)
    data = body.dict()
    data["created_by"] = data["created_by"] or user.get("name", "")
    rid = create_announcement(data)
    return {"id": rid}


# ── Operations: Instructors ───────────────────────────────────────────────────
@app.get("/api/operations/instructors")
async def api_instructors_get(request: Request, branch: str = ""):
    require_auth(request)
    conn = get_conn()
    cur  = conn.execute(
        "SELECT * FROM instructors WHERE branch=? AND is_active=1 ORDER BY name",
        (branch,)
    )
    rows = _rows(cur)
    conn.close()
    return rows


@app.post("/api/operations/instructors")
async def api_instructors_create(
    request:    Request,
    branch:     str        = Form(""),
    name:       str        = Form(...),
    english:    str        = Form(""),
    role:       str        = Form(""),
    bio:        str        = Form(""),
    tags:       str        = Form("[]"),
    classes:    str        = Form("[]"),
    curriculum: str        = Form(""),
    photo:      UploadFile = File(None),
):
    user = require_staff(request)
    photo_path = save_upload(photo) if photo and photo.filename else ""
    conn = get_conn()
    cur  = conn.execute(
        """INSERT INTO instructors (branch, name, english, role, bio, tags, classes, curriculum, photo_path)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (branch or user.get("branch", ""), name, english, role, bio,
         tags, classes, curriculum, photo_path)
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return {"id": rid}


class InstructorPatchBody(BaseModel):
    name:       Optional[str] = None
    english:    Optional[str] = None
    role:       Optional[str] = None
    bio:        Optional[str] = None
    tags:       Optional[str] = None
    classes:    Optional[str] = None
    curriculum: Optional[str] = None
    is_active:  Optional[int] = None


@app.patch("/api/operations/instructors/{instructor_id}")
async def api_instructors_patch(request: Request, instructor_id: int, body: InstructorPatchBody):
    require_staff(request)
    updates = {k: v for k, v in body.dict().items() if v is not None}
    if not updates:
        return {"ok": True}
    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn = get_conn()
    conn.execute(
        f"UPDATE instructors SET {set_clause} WHERE id=?",
        (*updates.values(), instructor_id)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


# ── Members API ────────────────────────────────────────────────────────────────
@app.get("/api/members")
async def api_members_list(request: Request, branch: str = "", q: str = "", status: str = ""):
    require_staff(request)
    return get_members(branch, status or None, q)


class MemberBody(BaseModel):
    branch:     str
    name:       str
    phone:      str = ""
    email:      str = ""
    birth_date: str = ""
    gender:     str = ""
    join_date:  str = ""
    status:     str = "active"
    pin:        str = ""
    note:       str = ""


@app.post("/api/members")
async def api_members_create(request: Request, body: MemberBody):
    require_staff(request)
    mid = upsert_member(body.dict())
    return {"id": mid}


@app.get("/api/members/{member_id}")
async def api_members_get(request: Request, member_id: int):
    require_staff(request)
    m = get_member(member_id)
    if not m:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다")
    return m


class MemberPatchBody(BaseModel):
    name:       Optional[str] = None
    phone:      Optional[str] = None
    email:      Optional[str] = None
    birth_date: Optional[str] = None
    gender:     Optional[str] = None
    status:     Optional[str] = None
    note:       Optional[str] = None


@app.patch("/api/members/{member_id}")
async def api_members_patch(request: Request, member_id: int, body: MemberPatchBody):
    require_staff(request)
    existing = get_member(member_id)
    if not existing:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다")
    updates = body.dict(exclude_none=True)
    merged  = {**existing, **updates, "id": member_id}
    upsert_member(merged)
    return {"ok": True}


@app.get("/api/members/{member_id}/memberships")
async def api_member_memberships(request: Request, member_id: int):
    require_staff(request)
    return get_member_memberships(member_id)


class MembershipBody(BaseModel):
    product_id:         Optional[int] = None
    product_name:       str = ""
    start_date:         str
    end_date:           Optional[str] = None
    remaining_sessions: int = 0
    paid_amount:        int = 0
    sold_by_name:       str = ""
    note:               str = ""


@app.post("/api/members/{member_id}/memberships")
async def api_member_memberships_create(request: Request, member_id: int, body: MembershipBody):
    require_staff(request)
    data = body.dict()
    data["member_id"] = member_id
    mid = create_membership(data)
    return {"id": mid}


# ── Classes API ────────────────────────────────────────────────────────────────
@app.get("/api/classes")
async def api_classes_get(request: Request, branch: str = ""):
    require_auth(request)
    return get_class_schedules(branch)


class ClassBody(BaseModel):
    branch:          str
    class_name:      str
    instructor_name: str = ""
    days:            str = ""
    start_time:      str
    end_time:        str
    capacity:        int = 20
    is_active:       int = 1


@app.post("/api/classes")
async def api_classes_create(request: Request, body: ClassBody):
    require_staff(request)
    rid = upsert_class_schedule(body.dict())
    return {"id": rid}


# ── ERP Bridge ────────────────────────────────────────────────────────────────
@app.get("/api/erp/pending-reports")
async def api_erp_pending(request: Request, branch: str = ""):
    require_auth(request)
    conn  = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")

    as_cur = conn.execute(
        "SELECT * FROM as_requests WHERE branch=? AND status='open' ORDER BY created_at DESC",
        (branch,)
    )
    as_requests = _rows(as_cur)

    sup_cur = conn.execute(
        "SELECT * FROM supply_requests WHERE branch=? AND status='pending' ORDER BY created_at DESC",
        (branch,)
    )
    supply_requests = _rows(sup_cur)

    att_count = conn.execute(
        """SELECT COUNT(*) FROM attendance a
           JOIN employees e ON a.employee_id=e.id
           WHERE e.branch=? AND a.work_date=? AND a.clock_in IS NOT NULL""",
        (branch, today)
    ).fetchone()[0]

    conn.close()
    return {
        "as_requests":      as_requests,
        "supply_requests":  supply_requests,
        "attendance_today": att_count,
    }


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("branch_server:app", host="0.0.0.0", port=8502, reload=True)
