"""Phase 3 — 회원 CRM (회원관리·회원권·수업예약)"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from domains.branch_app.db import (
    get_members, get_member, upsert_member,
    get_membership_products, upsert_membership_product,
    get_member_memberships, get_active_memberships,
    create_membership, hold_membership, expire_old_memberships,
    get_class_schedules, upsert_class_schedule,
    get_reservations, reserve_class, checkin_reservation,
)

_STATUS = {"active":"🟢 활성","hold":"⏸ 정지","expired":"⛔ 만료","withdrawn":"🚫 탈퇴"}
_GENDER = {"M":"남","F":"여","":""}


def render(user: dict):
    branch = user["branch"]
    name   = user["name"]
    expire_old_memberships()

    tab_list, tab_reg, tab_ms, tab_prod, tab_class = st.tabs(
        ["👥 회원 목록", "➕ 회원 등록", "💳 회원권 관리", "🏷 회원권 상품", "📚 수업 관리"]
    )

    # ════════════════════════════════════════
    # 회원 목록
    # ════════════════════════════════════════
    with tab_list:
        st.markdown("#### 회원 목록")
        c1, c2, c3 = st.columns([3, 2, 1])
        search    = c1.text_input("이름/전화번호 검색", placeholder="검색어 입력")
        st_filter = c2.selectbox("상태", ["","active","hold","expired","withdrawn"],
                                 format_func=lambda x: "전체" if not x else _STATUS.get(x,x))
        show_ms   = c3.checkbox("회원권 포함", value=False)

        members = get_members(branch, status=st_filter or None, search=search)
        if not members:
            st.info("검색 결과가 없습니다.")
        else:
            rows = []
            for m in members:
                row = {
                    "ID": m["id"], "이름": m["name"],
                    "전화번호": m["phone"] or "—",
                    "성별": _GENDER.get(m.get("gender",""),""),
                    "가입일": m["join_date"] or "—",
                    "상태": _STATUS.get(m["status"], m["status"]),
                }
                if show_ms:
                    ms_list = get_member_memberships(m["id"])
                    active  = next((x for x in ms_list if x["status"]=="active"), None)
                    row["회원권"] = active["product_name"] if active else "없음"
                    row["만료일"] = active["end_date"] if active else "—"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=400)
            st.caption(f"총 {len(members)}명")

        st.divider()
        st.markdown("##### 회원 정보 수정")
        mod_id = st.number_input("수정할 회원 ID", min_value=1, step=1, key="mod_mem_id")
        if st.button("불러오기", key="load_mem_btn"):
            m = get_member(int(mod_id))
            if m:
                st.session_state["editing_member"] = m
            else:
                st.error("해당 ID의 회원이 없습니다.")

        if "editing_member" in st.session_state:
            m = st.session_state["editing_member"]
            with st.form("edit_member_form"):
                st.markdown(f"**{m['name']}** (ID: {m['id']}) 수정")
                c1, c2 = st.columns(2)
                new_name   = c1.text_input("이름", value=m["name"])
                new_phone  = c2.text_input("전화번호", value=m.get("phone",""))
                c3, c4 = st.columns(2)
                new_email  = c3.text_input("이메일", value=m.get("email",""))
                new_status = c4.selectbox("상태", ["active","hold","expired","withdrawn"],
                                          index=["active","hold","expired","withdrawn"].index(m.get("status","active")),
                                          format_func=lambda x: _STATUS.get(x,x))
                new_note   = st.text_area("메모", value=m.get("note",""), height=60)
                if st.form_submit_button("저장", type="primary"):
                    upsert_member({**m, "name": new_name, "phone": new_phone,
                                   "email": new_email, "status": new_status, "note": new_note})
                    st.success("✅ 수정 완료")
                    del st.session_state["editing_member"]
                    st.rerun()

    # ════════════════════════════════════════
    # 회원 등록
    # ════════════════════════════════════════
    with tab_reg:
        st.markdown("#### 신규 회원 등록")
        with st.form("member_reg_form"):
            c1, c2 = st.columns(2)
            mem_name  = c1.text_input("이름 *")
            mem_phone = c2.text_input("전화번호 *", placeholder="010-0000-0000")
            c3, c4 = st.columns(2)
            mem_email  = c3.text_input("이메일")
            mem_birth  = c4.text_input("생년월일 (YYYY-MM-DD)")
            c5, c6 = st.columns(2)
            mem_gender = c5.radio("성별", ["","M","F"], format_func=lambda x: "미입력" if x=="" else ("남" if x=="M" else "여"),
                                   horizontal=True)
            mem_join   = c6.text_input("가입일", value=date.today().strftime("%Y-%m-%d"))
            mem_note   = st.text_area("메모", height=60)

            if st.form_submit_button("회원 등록", type="primary", use_container_width=True):
                if not mem_name or not mem_phone:
                    st.error("이름과 전화번호는 필수입니다.")
                else:
                    mid = upsert_member({
                        "branch": branch, "name": mem_name.strip(),
                        "phone": mem_phone.strip(), "email": mem_email.strip(),
                        "birth_date": mem_birth.strip(), "gender": mem_gender,
                        "join_date": mem_join.strip(), "note": mem_note.strip(),
                    })
                    st.success(f"✅ {mem_name} 회원 등록 완료 (ID: {mid})")
                    # 회원권 바로 등록 안내
                    st.info("💡 '회원권 관리' 탭에서 회원권을 등록하세요.")

    # ════════════════════════════════════════
    # 회원권 관리
    # ════════════════════════════════════════
    with tab_ms:
        st.markdown("#### 회원권 등록 / 현황")

        # 만료 임박 (7일 이내)
        all_ms  = get_active_memberships(branch)
        today_s = date.today().strftime("%Y-%m-%d")
        soon    = [m for m in all_ms if m.get("end_date") and m["end_date"] <= (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")]
        if soon:
            st.warning(f"⚠️ 만료 임박 ({len(soon)}명): " + ", ".join(m["member_name"] for m in soon))

        # 활성 회원권 테이블
        if all_ms:
            df = pd.DataFrame(all_ms)
            show = df[["member_name","member_phone","product_name","start_date","end_date",
                       "remaining_sessions","status"]].copy()
            show.columns = ["회원명","전화","회원권","시작일","만료일","잔여횟수","상태"]
            show["상태"] = show["상태"].map(_STATUS).fillna(show["상태"])
            st.dataframe(show, use_container_width=True, hide_index=True, height=300)

        st.divider()
        st.markdown("##### 회원권 등록")
        products = get_membership_products(branch)
        if not products:
            st.warning("등록된 회원권 상품이 없습니다. '회원권 상품' 탭에서 먼저 추가하세요.")
        else:
            members_all = get_members(branch)
            if not members_all:
                st.warning("등록된 회원이 없습니다.")
            else:
                with st.form("ms_reg_form"):
                    c1, c2 = st.columns(2)
                    mem_opts = {m["id"]: f"{m['name']} ({m['phone'] or '—'})" for m in members_all}
                    mem_sel  = c1.selectbox("회원 *", list(mem_opts.keys()),
                                            format_func=lambda x: mem_opts[x])
                    prod_opts = {p["id"]: f"{p['name']} ({p['price']:,}원, {p['duration_days']}일)" for p in products}
                    prod_sel  = c2.selectbox("회원권 상품 *", list(prod_opts.keys()),
                                             format_func=lambda x: prod_opts[x])
                    c3, c4, c5 = st.columns([2, 2, 2])
                    start_date = c3.text_input("시작일", value=date.today().strftime("%Y-%m-%d"))
                    paid_amt   = c4.number_input("실결제금액", min_value=0, step=1000)
                    ms_note    = c5.text_input("메모")

                    if st.form_submit_button("회원권 등록", type="primary", use_container_width=True):
                        prod  = next(p for p in products if p["id"] == prod_sel)
                        try:
                            s = date.fromisoformat(start_date)
                            e = s + timedelta(days=prod["duration_days"])
                            end_date = e.strftime("%Y-%m-%d")
                        except Exception:
                            end_date = None
                        create_membership({
                            "member_id": mem_sel, "product_id": prod_sel,
                            "product_name": prod["name"], "start_date": start_date,
                            "end_date": end_date,
                            "remaining_sessions": prod.get("sessions",0),
                            "paid_amount": int(paid_amt),
                            "sold_by_name": name, "note": ms_note,
                        })
                        st.success(f"✅ 회원권 등록 완료 (만료: {end_date})")
                        st.rerun()

        st.divider()
        st.markdown("##### 회원권 일시정지")
        with st.form("hold_form"):
            c1, c2, c3 = st.columns(3)
            hold_ms_id  = c1.number_input("회원권 ID", min_value=1, step=1)
            hold_start  = c2.text_input("정지 시작일", value=date.today().strftime("%Y-%m-%d"))
            hold_end    = c3.text_input("정지 종료일")
            if st.form_submit_button("정지 처리"):
                if not hold_end:
                    st.error("종료일을 입력하세요.")
                else:
                    hold_membership(int(hold_ms_id), hold_start, hold_end)
                    st.success("✅ 정지 처리 완료 (만료일 자동 연장)")
                    st.rerun()

    # ════════════════════════════════════════
    # 회원권 상품
    # ════════════════════════════════════════
    with tab_prod:
        st.markdown("#### 회원권 상품 관리")
        products = get_membership_products(branch, active_only=False)
        if products:
            df = pd.DataFrame(products)
            show = df[["id","name","product_type","duration_days","sessions","price","is_active"]].copy()
            show.columns = ["ID","상품명","유형","기간(일)","횟수","가격","활성"]
            show["유형"] = show["유형"].map({"period":"기간제","session":"횟수제","mixed":"혼합"}).fillna(show["유형"])
            show["가격"] = show["가격"].apply(lambda v: f"{int(v):,}원")
            show["활성"] = show["활성"].apply(lambda v: "✅" if v else "❌")
            st.dataframe(show, use_container_width=True, hide_index=True)

        st.divider()
        with st.form("prod_form"):
            st.markdown("##### 상품 추가 / 수정")
            c1, c2 = st.columns([1, 3])
            edit_id   = c1.number_input("ID (수정 시)", min_value=0, step=1, value=0)
            prod_name = c2.text_input("상품명 *")
            c3, c4, c5, c6 = st.columns(4)
            ptype    = c3.selectbox("유형", ["period","session","mixed"],
                                    format_func=lambda x: {"period":"기간제","session":"횟수제","mixed":"혼합"}[x])
            duration = c4.number_input("기간(일)", min_value=0, value=30)
            sessions = c5.number_input("횟수 (0=무제한)", min_value=0, value=0)
            price    = c6.number_input("가격(원)", min_value=0, step=1000)
            is_active = st.checkbox("활성", value=True)
            if st.form_submit_button("저장", type="primary", use_container_width=True):
                if not prod_name:
                    st.error("상품명을 입력하세요.")
                else:
                    upsert_membership_product({
                        "id": int(edit_id) if edit_id else None,
                        "branch": branch, "name": prod_name,
                        "product_type": ptype, "duration_days": int(duration),
                        "sessions": int(sessions), "price": int(price),
                        "is_active": 1 if is_active else 0,
                    })
                    st.success("✅ 저장 완료")
                    st.rerun()

    # ════════════════════════════════════════
    # 수업 관리
    # ════════════════════════════════════════
    with tab_class:
        st.markdown("#### 수업 시간표 & 예약")
        sub_sch, sub_res = st.tabs(["시간표 관리", "예약 / 출석"])

        with sub_sch:
            schedules = get_class_schedules(branch, active_only=False)
            if schedules:
                df = pd.DataFrame(schedules)
                show = df[["id","class_name","instructor_name","days","start_time","end_time","capacity","is_active"]].copy()
                show.columns = ["ID","수업명","강사","요일","시작","종료","정원","활성"]
                show["활성"] = show["활성"].apply(lambda v: "✅" if v else "❌")
                st.dataframe(show, use_container_width=True, hide_index=True)

            with st.form("class_sch_form"):
                st.markdown("##### 수업 추가 / 수정")
                c1, c2 = st.columns([1, 3])
                sch_id   = c1.number_input("ID (수정 시)", min_value=0, step=1, value=0)
                cls_name = c2.text_input("수업명 *")
                c3, c4, c5, c6, c7 = st.columns(5)
                instr   = c3.text_input("강사명")
                days    = c4.text_input("요일", placeholder="월수금")
                stime   = c5.text_input("시작", placeholder="10:00")
                etime   = c6.text_input("종료", placeholder="11:00")
                cap     = c7.number_input("정원", min_value=1, value=20)
                active  = st.checkbox("활성", value=True)
                if st.form_submit_button("저장", type="primary", use_container_width=True):
                    if not cls_name or not stime or not etime:
                        st.error("수업명, 시작/종료 시간은 필수입니다.")
                    else:
                        upsert_class_schedule({
                            "id": int(sch_id) if sch_id else None,
                            "branch": branch, "class_name": cls_name,
                            "instructor_name": instr, "days": days,
                            "start_time": stime, "end_time": etime,
                            "capacity": int(cap), "is_active": 1 if active else 0,
                        })
                        st.success("✅ 저장 완료")
                        st.rerun()

        with sub_res:
            schedules = get_class_schedules(branch)
            if not schedules:
                st.info("등록된 수업이 없습니다.")
            else:
                members_all = get_members(branch)
                c1, c2 = st.columns(2)
                sch_opts = {s["id"]: f"{s['class_name']} ({s['start_time']}~{s['end_time']}, {s['days']})" for s in schedules}
                sel_sch  = c1.selectbox("수업 선택", list(sch_opts.keys()),
                                        format_func=lambda x: sch_opts[x])
                sel_date = c2.text_input("날짜", value=date.today().strftime("%Y-%m-%d"))

                res_list = get_reservations(sel_sch, sel_date)
                sel_sch_obj = next(s for s in schedules if s["id"] == sel_sch)
                st.markdown(f"**예약 현황**: {len(res_list)} / {sel_sch_obj['capacity']}명")

                if res_list:
                    for r in res_list:
                        col_a, col_b, col_c = st.columns([3, 2, 2])
                        status_emoji = {"reserved":"🟡","checked_in":"✅","cancelled":"❌","no_show":"⛔"}.get(r["status"],"—")
                        col_a.markdown(f"{status_emoji} **{r['member_name']}** {r.get('member_phone','')}")
                        col_b.markdown(f"예약: {r['created_at'][:10]}")
                        if r["status"] == "reserved":
                            if col_c.button("출석체크", key=f"checkin_{r['id']}"):
                                checkin_reservation(r["id"])
                                st.rerun()

                st.divider()
                st.markdown("##### 예약 추가")
                with st.form("res_form"):
                    if not members_all:
                        st.warning("등록된 회원이 없습니다.")
                    else:
                        mem_opts = {m["id"]: f"{m['name']} ({m['phone'] or '—'})" for m in members_all}
                        mem_sel  = st.selectbox("회원", list(mem_opts.keys()),
                                                format_func=lambda x: mem_opts[x])
                        if st.form_submit_button("예약 등록", type="primary", use_container_width=True):
                            mem = next(m for m in members_all if m["id"] == mem_sel)
                            ok, msg = reserve_class(sel_sch, mem_sel, mem["name"], sel_date)
                            if ok:
                                st.success(f"✅ {mem['name']} 예약 완료")
                                st.rerun()
                            else:
                                st.error(msg)
