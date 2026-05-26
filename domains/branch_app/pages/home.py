"""Phase 1 — 홈 (출퇴근 + 이번달 요약)"""
import streamlit as st
from datetime import datetime, date
import calendar


_WEEKDAY = ["월", "화", "수", "목", "금", "토", "일"]


def _fmt(m: int) -> str:
    h, mn = divmod(m, 60)
    return f"{h}h {mn:02d}m"


def _elapsed(ci: str, today: date) -> str:
    try:
        ci_dt = datetime.strptime(f"{today} {ci}", "%Y-%m-%d %H:%M")
        mins  = max(0, int((datetime.now() - ci_dt).total_seconds() / 60))
        return _fmt(mins)
    except Exception:
        return "-"


def render(user: dict):
    from domains.payroll.db import (
        get_attendance_record, attendance_clock_in,
        attendance_clock_out, get_monthly_attendance,
    )
    today    = date.today()
    now      = datetime.now()
    wd       = today.strftime("%Y-%m-%d")
    now_hm   = now.strftime("%H:%M")
    rec      = get_attendance_record(user["employee_id"], wd)
    ci       = rec.get("clock_in")  if rec else None
    co       = rec.get("clock_out") if rec else None

    # ── 출퇴근 카드 ─────────────────────────────────────────
    st.markdown(f"""
    <div style='background:#fff;border:1px solid #e8e8e8;border-radius:14px;padding:1.2rem 1.4rem;margin-bottom:1rem;'>
        <div style='font-size:.82rem;color:#888;margin-bottom:.3rem;'>
            {today.strftime('%Y년 %m월 %d일')} ({_WEEKDAY[today.weekday()]})
        </div>
        <div style='font-size:1.6rem;font-weight:800;color:#1a1a2e;'>
            {'⏳ 출근 전' if not ci else ('🟢 근무 중' if not co else '✅ 퇴근 완료')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not ci:
        col_l, col_m, col_r = st.columns([1, 3, 1])
        with col_m:
            if st.button("🟢  출근하기", use_container_width=True, type="primary", key="btn_ci"):
                ok, msg = attendance_clock_in(user["employee_id"], wd, now_hm)
                if ok:
                    st.success(f"✅ 출근 완료 ({msg})")
                    st.rerun()
                else:
                    st.error(msg)

    elif not co:
        st.markdown(f"""
        <div style='text-align:center;background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                    padding:.7rem;margin-bottom:.8rem;font-size:.95rem;'>
            출근 <b>{ci}</b> &nbsp;|&nbsp; 근무 <b>{_elapsed(ci, today)}</b>
        </div>
        """, unsafe_allow_html=True)
        col_l, col_m, col_r = st.columns([1, 3, 1])
        with col_m:
            if st.button("🔴  퇴근하기", use_container_width=True, key="btn_co"):
                ok, msg = attendance_clock_out(
                    user["employee_id"], wd, now_hm,
                    user.get("work_start","09:00")
                )
                if ok:
                    st.success(f"✅ 퇴근 완료 ({msg})")
                    st.rerun()
                else:
                    st.error(msg)
    else:
        wm = rec.get("work_minutes",0) if rec else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("출근", ci or "-")
        c2.metric("퇴근", co or "-")
        c3.metric("근무시간", _fmt(wm))

    # ── 이번달 요약 ─────────────────────────────────────────
    st.divider()
    records     = get_monthly_attendance(user["employee_id"], today.year, today.month)
    worked_days = len([r for r in records if r.get("clock_in")])
    total_min   = sum(r.get("work_minutes",0) for r in records)
    late_cnt    = len([r for r in records if r.get("status") == "late"])

    st.markdown("#### 이번달 요약")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""<div style='background:#fff;border:1px solid #e8e8e8;border-radius:10px;
        padding:.8rem;text-align:center;'>
        <div style='font-size:1.5rem;font-weight:800;color:#c8253c;'>{worked_days}</div>
        <div style='font-size:.75rem;color:#888;margin-top:2px;'>근무일</div></div>""",
        unsafe_allow_html=True)
    c2.markdown(f"""<div style='background:#fff;border:1px solid #e8e8e8;border-radius:10px;
        padding:.8rem;text-align:center;'>
        <div style='font-size:1.5rem;font-weight:800;color:#c8253c;'>{_fmt(total_min)}</div>
        <div style='font-size:.75rem;color:#888;margin-top:2px;'>총 근로시간</div></div>""",
        unsafe_allow_html=True)
    c3.markdown(f"""<div style='background:#fff;border:1px solid #e8e8e8;border-radius:10px;
        padding:.8rem;text-align:center;'>
        <div style='font-size:1.5rem;font-weight:800;color:#c8253c;'>{late_cnt}회</div>
        <div style='font-size:.75rem;color:#888;margin-top:2px;'>지각</div></div>""",
        unsafe_allow_html=True)

    # ── 달력 ────────────────────────────────────────────────
    st.markdown(f"#### {today.month}월 근태 달력")
    rec_map     = {r["work_date"]: r for r in records}
    _, num_days = calendar.monthrange(today.year, today.month)
    first_wday  = date(today.year, today.month, 1).weekday()

    cols = st.columns(7)
    for i, d in enumerate(["월","화","수","목","금","토","일"]):
        color = "#c8253c" if i >= 5 else "#555"
        cols[i].markdown(f"<div style='text-align:center;font-weight:700;color:{color};font-size:.78rem'>{d}</div>",
                         unsafe_allow_html=True)

    cells: list[str] = [""] * first_wday
    for day in range(1, num_days + 1):
        d_str = f"{today.year}-{today.month:02d}-{day:02d}"
        d_obj = date(today.year, today.month, day)
        r     = rec_map.get(d_str)
        is_today = (d_obj == today)
        border = "border:2px solid #c8253c;" if is_today else ""

        if d_obj.weekday() >= 5:
            bg, txt = "#f5f5f5", "#bbb"
        elif r and r.get("clock_in"):
            status = r.get("status","present")
            bg  = "#c8e6c9" if status == "present" else "#fff9c4"
            txt = "#1b5e20" if status == "present" else "#f57f17"
        elif d_obj < today:
            bg, txt = "#ffcdd2", "#b71c1c"
        else:
            bg, txt = "#f9f9f9", "#bbb"

        cells.append(f'<div style="background:{bg};color:{txt};{border}border-radius:50%;'
                     f'width:32px;height:32px;line-height:32px;text-align:center;'
                     f'font-size:.82rem;font-weight:600;margin:2px auto;">{day}</div>')

    while len(cells) % 7 != 0:
        cells.append("")

    for week_start in range(0, len(cells), 7):
        week = cells[week_start:week_start + 7]
        cols = st.columns(7)
        for i, cell in enumerate(week):
            cols[i].markdown(cell, unsafe_allow_html=True)
