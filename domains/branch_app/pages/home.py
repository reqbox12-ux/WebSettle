"""Phase 1 — 홈 (GPS 출퇴근 + 휴게 + 급여 달력)"""
import math
import streamlit as st
from datetime import datetime, date
import calendar

_WEEKDAY = ["월", "화", "수", "목", "금", "토", "일"]

_GPS_JS = """
await new Promise((resolve) => {
    if (!navigator.geolocation) { resolve(null); return; }
    navigator.geolocation.getCurrentPosition(
        (p) => resolve({lat: p.coords.latitude, lng: p.coords.longitude,
                        acc: Math.round(p.coords.accuracy)}),
        () => resolve(null),
        {enableHighAccuracy: true, timeout: 8000, maximumAge: 60000}
    );
});
"""


def _fmt(m: int) -> str:
    h, mn = divmod(abs(int(m)), 60)
    return f"{h}h {mn:02d}m"


def _fw(v: int) -> str:
    return f"{v:,}"


def _elapsed(ci: str, today: date) -> str:
    try:
        ci_dt = datetime.strptime(f"{today} {ci}", "%Y-%m-%d %H:%M")
        mins  = max(0, int((datetime.now() - ci_dt).total_seconds() / 60))
        return _fmt(mins)
    except Exception:
        return "-"


def _haversine_m(lat1, lng1, lat2, lng2) -> float:
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a  = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _check_gps(branch_lat, branch_lng, branch_radius) -> tuple[bool, str]:
    if not branch_lat or not branch_lng:
        return True, "no_coords"
    try:
        from streamlit_javascript import st_javascript
        loc = st_javascript(_GPS_JS)
    except ImportError:
        return True, "no_lib"
    if loc == 0:
        return False, "loading"
    if not loc or not isinstance(loc, dict):
        return False, "denied"
    dist = _haversine_m(branch_lat, branch_lng, loc["lat"], loc["lng"])
    return (dist <= branch_radius), f"{dist:.0f}m"


def render(user: dict):
    from domains.payroll.db import (
        get_attendance_record, attendance_clock_in,
        attendance_clock_out, attendance_break_start, attendance_break_end,
        get_monthly_attendance, calc_and_save_daily_pay,
        get_daily_pay_records, get_monthly_pay_total,
    )
    from domains.branch.db import get_branch_by_name

    today  = date.today()
    now    = datetime.now()
    wd     = today.strftime("%Y-%m-%d")
    now_hm = now.strftime("%H:%M")

    branch_info   = get_branch_by_name(user["branch"]) or {}
    branch_lat    = branch_info.get("lat")
    branch_lng    = branch_info.get("lng")
    branch_radius = int(branch_info.get("attendance_radius") or 300)

    rec = get_attendance_record(user["employee_id"], wd)
    ci  = rec.get("clock_in")    if rec else None
    co  = rec.get("clock_out")   if rec else None
    bks = rec.get("break_start") if rec else None
    brk = rec.get("break_minutes", 0) if rec else 0

    # ── 상태 카드 ─────────────────────────────────────────────
    if not ci:
        status_txt, status_col = "⏳ 출근 전",     "#6b7280"
    elif bks:
        status_txt, status_col = "☕ 휴게 중",     "#d97706"
    elif not co:
        status_txt, status_col = "🟢 근무 중",     "#16a34a"
    else:
        status_txt, status_col = "✅ 퇴근 완료",   "#2563eb"

    st.markdown(f"""
    <div style='background:#fff;border:1px solid #e5e7eb;border-radius:14px;
                padding:1.2rem 1.4rem;margin-bottom:1rem;'>
        <div style='font-size:.82rem;color:#9ca3af;margin-bottom:.3rem;'>
            {today.strftime('%Y년 %m월 %d일')} ({_WEEKDAY[today.weekday()]})
        </div>
        <div style='font-size:1.5rem;font-weight:800;color:{status_col};'>{status_txt}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── GPS 확인 ─────────────────────────────────────────────
    gps_ok, gps_msg = _check_gps(branch_lat, branch_lng, branch_radius)
    if gps_msg == "loading":
        st.info("📍 위치 확인 중... 잠시 기다려주세요.")
        return
    if not gps_ok:
        if gps_msg == "denied":
            st.error("📍 GPS를 사용할 수 없습니다. 브라우저 위치 권한을 허용해주세요.")
        else:
            st.error(
                f"📍 현재 위치가 지점에서 **{gps_msg}** 떨어져 있습니다.  \n"
                f"허용 반경 **{branch_radius}m** 이내에서만 출퇴근할 수 있습니다."
            )
        return
    if gps_msg not in ("no_coords", "no_lib") and branch_lat:
        st.caption(f"📍 위치 확인됨 · 지점까지 {gps_msg} (허용 {branch_radius}m)")

    # ── 근태 버튼 ─────────────────────────────────────────────
    if not ci:
        col_l, col_m, col_r = st.columns([1, 3, 1])
        with col_m:
            if st.button("🟢  출 근", use_container_width=True, type="primary", key="btn_ci"):
                ok, msg = attendance_clock_in(user["employee_id"], wd, now_hm)
                if ok:
                    st.success(f"✅ 출근 완료 ({msg})")
                    st.rerun()
                else:
                    st.error(msg)

    elif co:
        wm  = rec.get("work_minutes", 0) if rec else 0
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("출근", ci or "-")
        col_b.metric("퇴근", co or "-")
        col_c.metric("근무", _fmt(wm))
        col_d.metric("휴게", _fmt(brk))

        # 오늘 급여 (시급제인 경우)
        pay_rec = get_daily_pay_records(user["employee_id"], today.year, today.month)
        today_pay = next((p for p in pay_rec if p["work_date"] == wd), None)
        if today_pay and today_pay["total_pay"] > 0:
            badge = " 🏖️ 휴일" if (today_pay["is_weekend"] or today_pay["is_holiday"]) else ""
            extra = f" (+야간 {_fw(today_pay['extra_pay'])}원)" if today_pay["extra_pay"] else ""
            st.info(f"💰 오늘 급여: **{_fw(today_pay['total_pay'])}원**{extra}{badge}")

    else:
        elapsed = _elapsed(ci, today)
        bk_min  = brk or 0

        if bks:
            bk_elapsed = _elapsed(bks, today)
            st.markdown(f"""
            <div style='text-align:center;background:#fef9c3;border:1px solid #fde047;
                        border-radius:10px;padding:.7rem;margin-bottom:.8rem;font-size:.95rem;'>
                출근 <b>{ci}</b> &nbsp;|&nbsp; 휴게시작 <b>{bks}</b>
                &nbsp;|&nbsp; 휴게 <b>{bk_elapsed}</b>
            </div>
            """, unsafe_allow_html=True)
            col_b, col_c = st.columns(2)
            with col_b:
                if st.button("▶  휴게 종료", use_container_width=True, type="primary", key="btn_bke"):
                    ok, msg = attendance_break_end(user["employee_id"], wd, now_hm)
                    if ok:
                        st.success(f"☕ 휴게 종료 ({msg})")
                        st.rerun()
                    else:
                        st.error(msg)
            with col_c:
                if st.button("🔴  퇴 근", use_container_width=True, key="btn_co_b"):
                    ok, msg = attendance_clock_out(user["employee_id"], wd, now_hm,
                                                   user.get("work_start", "09:00"))
                    if ok:
                        calc_and_save_daily_pay(user["employee_id"], wd)
                        st.success(f"✅ 퇴근 완료 ({msg})")
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.markdown(f"""
            <div style='text-align:center;background:#f0fdf4;border:1px solid #86efac;
                        border-radius:10px;padding:.7rem;margin-bottom:.8rem;font-size:.95rem;'>
                출근 <b>{ci}</b> &nbsp;|&nbsp; 근무 <b>{elapsed}</b>
                {f'&nbsp;|&nbsp; 누적 휴게 <b>{_fmt(bk_min)}</b>' if bk_min else ''}
            </div>
            """, unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("☕  휴 게", use_container_width=True, key="btn_bks"):
                    ok, msg = attendance_break_start(user["employee_id"], wd, now_hm)
                    if ok:
                        st.info(f"☕ 휴게 시작 ({msg})")
                        st.rerun()
                    else:
                        st.error(msg)
            with col_b:
                if st.button("🔴  퇴 근", use_container_width=True, key="btn_co"):
                    ok, msg = attendance_clock_out(user["employee_id"], wd, now_hm,
                                                   user.get("work_start", "09:00"))
                    if ok:
                        calc_and_save_daily_pay(user["employee_id"], wd)
                        st.success(f"✅ 퇴근 완료 ({msg})")
                        st.rerun()
                    else:
                        st.error(msg)

    # ── 이번달 요약 ───────────────────────────────────────────
    st.divider()
    records     = get_monthly_attendance(user["employee_id"], today.year, today.month)
    pay_records = get_daily_pay_records(user["employee_id"], today.year, today.month)
    pay_map     = {p["work_date"]: p for p in pay_records}
    monthly_pay = get_monthly_pay_total(user["employee_id"], today.year, today.month)

    worked_days = len([r for r in records if r.get("clock_in")])
    total_min   = sum(r.get("work_minutes", 0) for r in records)
    break_total = sum(r.get("break_minutes", 0) for r in records)
    late_cnt    = len([r for r in records if r.get("status") == "late"])

    st.markdown("#### 이번달 요약")
    cols_s = st.columns(4 if not monthly_pay else 5)
    for col, val, lbl in [
        (cols_s[0], str(worked_days),  "근무일"),
        (cols_s[1], _fmt(total_min),   "총 근로시간"),
        (cols_s[2], _fmt(break_total), "총 휴게시간"),
        (cols_s[3], f"{late_cnt}회",   "지각"),
    ]:
        col.markdown(
            f'<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;'
            f'padding:.8rem;text-align:center;">'
            f'<div style="font-size:1.3rem;font-weight:800;color:#c8253c;">{val}</div>'
            f'<div style="font-size:.75rem;color:#9ca3af;margin-top:2px;">{lbl}</div></div>',
            unsafe_allow_html=True,
        )
    if monthly_pay:
        cols_s[4].markdown(
            f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;'
            f'padding:.8rem;text-align:center;">'
            f'<div style="font-size:1.1rem;font-weight:800;color:#16a34a;">'
            f'{_fw(monthly_pay)}원</div>'
            f'<div style="font-size:.75rem;color:#9ca3af;margin-top:2px;">이번달 예상급여</div></div>',
            unsafe_allow_html=True,
        )

    # ── 급여 달력 ─────────────────────────────────────────────
    st.markdown(f"#### {today.month}월 근태 · 급여 달력")
    rec_map     = {r["work_date"]: r for r in records}
    _, num_days = calendar.monthrange(today.year, today.month)
    first_wday  = date(today.year, today.month, 1).weekday()

    day_cols = st.columns(7)
    for i, d in enumerate(["월","화","수","목","금","토","일"]):
        color = "#c8253c" if i >= 5 else "#555"
        day_cols[i].markdown(
            f"<div style='text-align:center;font-weight:700;color:{color};font-size:.78rem'>{d}</div>",
            unsafe_allow_html=True,
        )

    cells: list[str] = [""] * first_wday
    for day in range(1, num_days + 1):
        d_str  = f"{today.year}-{today.month:02d}-{day:02d}"
        d_obj  = date(today.year, today.month, day)
        r      = rec_map.get(d_str)
        p      = pay_map.get(d_str)
        border = "border:2px solid #c8253c;" if d_obj == today else ""

        is_wknd = d_obj.weekday() >= 5
        if is_wknd:
            bg, txt = "#f5f5f5", "#bbb"
        elif r and r.get("clock_in"):
            status = r.get("status", "present")
            if status == "late":
                bg, txt = "#fff9c4", "#f57f17"
            else:
                bg, txt = "#c8e6c9", "#1b5e20"
        elif d_obj < today:
            bg, txt = "#ffcdd2", "#b71c1c"
        else:
            bg, txt = "#f9f9f9", "#bbb"

        # 급여 표시 (있을 때)
        pay_html = ""
        if p and p["total_pay"] > 0:
            hol_flag = "🏖" if (p["is_weekend"] or p["is_holiday"]) else ""
            pay_html = (
                f'<div style="font-size:9px;color:#16a34a;font-weight:700;'
                f'white-space:nowrap;overflow:hidden;margin-top:1px;">'
                f'{hol_flag}{_fw(p["total_pay"])}</div>'
            )
        # 근무시간 표시
        time_html = ""
        if r and r.get("work_minutes"):
            time_html = (
                f'<div style="font-size:9px;color:#555;margin-top:1px;">'
                f'{_fmt(r["work_minutes"])}</div>'
            )

        cells.append(
            f'<div style="background:{bg};color:{txt};{border}border-radius:6px;'
            f'min-height:52px;padding:3px 4px;text-align:center;'
            f'font-size:.82rem;font-weight:600;margin:2px;">'
            f'{day}{time_html}{pay_html}</div>'
        )

    while len(cells) % 7 != 0:
        cells.append("")

    for week_start in range(0, len(cells), 7):
        week     = cells[week_start:week_start + 7]
        week_col = st.columns(7)
        for i, cell in enumerate(week):
            week_col[i].markdown(cell, unsafe_allow_html=True)
