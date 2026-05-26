"""Phase 5 — 알리고 SMS 문자 발송"""
import streamlit as st
import pandas as pd
from datetime import date
from domains.branch_app.db import (
    get_aligo_config, save_aligo_config, aligo_send, aligo_send_bulk,
    get_sms_templates, upsert_sms_template,
    get_sms_logs, log_sms,
    get_auto_sms_rules, upsert_auto_sms_rule, run_auto_sms,
    get_members, get_active_memberships,
)


def render(user: dict):
    branch = user["branch"]
    name   = user["name"]

    tab_send, tab_bulk, tab_tpl, tab_auto, tab_log, tab_cfg = st.tabs(
        ["📱 단건 발송", "📨 대량 발송", "📝 템플릿", "⚙️ 자동발송", "📋 발송 이력", "🔑 Aligo 설정"]
    )

    cfg = get_aligo_config()
    is_configured = bool(cfg.get("api_key") and cfg.get("user_id") and cfg.get("sender"))

    if not is_configured:
        st.warning("⚠️ Aligo API가 설정되지 않았습니다. **Aligo 설정** 탭에서 API 키를 먼저 입력하세요.")

    # ════════════════════════════════════════
    # 단건 발송
    # ════════════════════════════════════════
    with tab_send:
        st.markdown("#### 개별 문자 발송")
        templates = get_sms_templates()
        members   = get_members(branch)

        with st.form("single_sms_form"):
            c1, c2 = st.columns([3, 2])

            # 회원 선택 or 직접 입력
            use_member = c1.checkbox("회원 선택")
            if use_member and members:
                mem_opts = {str(m["id"]): f"{m['name']} ({m['phone'] or '—'})" for m in members}
                mem_sel  = st.selectbox("회원 선택", list(mem_opts.keys()),
                                        format_func=lambda x: mem_opts[x])
                mem = next(m for m in members if str(m["id"]) == mem_sel)
                recv_phone = mem["phone"]
                recv_name  = mem["name"]
            else:
                recv_phone = c1.text_input("수신 전화번호 *", placeholder="010-0000-0000")
                recv_name  = c2.text_input("수신자 이름")

            # 템플릿 선택
            tpl_opts = {"": "직접 입력"} | {str(t["id"]): t["name"] for t in templates}
            tpl_sel  = st.selectbox("템플릿 선택 (선택)", list(tpl_opts.keys()),
                                    format_func=lambda x: tpl_opts[x])
            default_msg = ""
            if tpl_sel:
                tpl = next((t for t in templates if str(t["id"]) == tpl_sel), None)
                if tpl:
                    default_msg = tpl["content"].replace("{이름}", recv_name or "").replace("{지점명}", branch)

            msg   = st.text_area("메시지 내용 *", value=default_msg, height=120,
                                  help="90자 이하: SMS, 91자 이상: LMS 자동 전환")
            title = st.text_input("제목 (LMS/MMS용)", placeholder="메시지가 90자 초과 시 사용")

            st.markdown(f"<div style='color:#888;font-size:.8rem;'>글자수: {len(msg)} / 90 (초과 시 LMS 자동 전환)</div>",
                        unsafe_allow_html=True)

            submitted = st.form_submit_button("문자 발송", type="primary", use_container_width=True,
                                              disabled=not is_configured)
            if submitted:
                if not recv_phone or not msg:
                    st.error("전화번호와 메시지를 입력하세요.")
                else:
                    res = aligo_send(recv_phone, msg, title)
                    if res.get("result_code") == "1":
                        log_sms(recv_phone, recv_name, msg, "sent",
                                int(tpl_sel) if tpl_sel else None,
                                str(res.get("msg_id","")), "", name)
                        st.success(f"✅ 발송 완료 (메시지ID: {res.get('msg_id','')})")
                    else:
                        log_sms(recv_phone, recv_name, msg, "failed",
                                int(tpl_sel) if tpl_sel else None, "", res.get("message",""), name)
                        st.error(f"❌ 발송 실패: {res.get('message','알 수 없는 오류')}")

    # ════════════════════════════════════════
    # 대량 발송
    # ════════════════════════════════════════
    with tab_bulk:
        st.markdown("#### 대량 문자 발송")
        templates = get_sms_templates()
        members   = get_members(branch)

        if not members:
            st.info("등록된 회원이 없습니다.")
        else:
            c1, c2 = st.columns(2)
            status_filter = c1.multiselect("회원 상태 필터",
                                            ["active","hold","expired"],
                                            default=["active"],
                                            format_func=lambda x: {"active":"활성","hold":"정지","expired":"만료"}[x])
            filtered = [m for m in members if m["status"] in status_filter and m.get("phone")]

            st.markdown(f"**대상 인원: {len(filtered)}명** (전화번호 있는 회원)")

            if filtered:
                df = pd.DataFrame(filtered)[["name","phone","status"]]
                df.columns = ["이름","전화번호","상태"]
                st.dataframe(df, use_container_width=True, hide_index=True, height=200)

            tpl_opts = {"": "직접 입력"} | {str(t["id"]): t["name"] for t in templates}
            tpl_sel  = st.selectbox("템플릿", list(tpl_opts.keys()),
                                    format_func=lambda x: tpl_opts[x], key="bulk_tpl")
            default_msg = ""
            if tpl_sel:
                tpl = next((t for t in templates if str(t["id"]) == tpl_sel), None)
                if tpl:
                    default_msg = tpl["content"]

            bulk_msg   = st.text_area("메시지 내용 *", value=default_msg, height=120,
                                      help="변수: {이름}, {지점명}, {만료일}")
            bulk_title = st.text_input("제목 (LMS용)")

            if st.button(f"📨 {len(filtered)}명에게 발송", type="primary",
                         disabled=not is_configured or not filtered or not bulk_msg):
                with st.spinner(f"{len(filtered)}명에게 발송 중..."):
                    targets = [{"phone": m["phone"], "name": m["name"], "지점명": branch}
                               for m in filtered]
                    results = aligo_send_bulk(targets, bulk_msg, bulk_title)
                    sent_ok = sum(1 for r in results if r["status"] == "sent")
                    sent_fail = len(results) - sent_ok
                    st.success(f"✅ 발송 완료: {sent_ok}명 성공 / {sent_fail}명 실패")
                    if sent_fail:
                        fails = [r["name"] for r in results if r["status"] == "failed"]
                        st.warning(f"실패: {', '.join(fails)}")

    # ════════════════════════════════════════
    # 템플릿 관리
    # ════════════════════════════════════════
    with tab_tpl:
        st.markdown("#### 문자 템플릿 관리")
        templates = get_sms_templates(active_only=False)
        if templates:
            df = pd.DataFrame(templates)
            show = df[["id","name","content","sms_type","is_active"]].copy()
            show.columns = ["ID","템플릿명","내용","유형","활성"]
            show["활성"] = show["활성"].apply(lambda v: "✅" if v else "❌")
            show["내용"] = show["내용"].str[:40] + "..."
            st.dataframe(show, use_container_width=True, hide_index=True)

        st.divider()
        st.info("""
        **사용 가능한 변수:**
        `{이름}` `{지점명}` `{만료일}` `{잔여횟수}` `{전화번호}`
        """)
        with st.form("tpl_form"):
            st.markdown("##### 템플릿 추가 / 수정")
            c1, c2 = st.columns([1, 3])
            tpl_id    = c1.number_input("ID (수정 시)", min_value=0, step=1, value=0)
            tpl_name  = c2.text_input("템플릿명 *")
            tpl_content = st.text_area("내용 *", height=120, placeholder="{이름}님, 안녕하세요. {지점명}입니다.")
            c3, c4 = st.columns(2)
            tpl_type   = c3.selectbox("유형", ["SMS","LMS","MMS"],
                                       help="SMS: 90자 이하, LMS: 2000자 이하")
            tpl_active = c4.checkbox("활성", value=True)
            if st.form_submit_button("저장", type="primary", use_container_width=True):
                if not tpl_name or not tpl_content:
                    st.error("템플릿명과 내용을 입력하세요.")
                else:
                    upsert_sms_template({
                        "id": int(tpl_id) if tpl_id else None,
                        "name": tpl_name, "content": tpl_content,
                        "sms_type": tpl_type, "is_active": 1 if tpl_active else 0,
                    })
                    st.success("✅ 저장 완료")
                    st.rerun()

    # ════════════════════════════════════════
    # 자동 발송 설정
    # ════════════════════════════════════════
    with tab_auto:
        st.markdown("#### 자동 발송 규칙")
        templates = get_sms_templates()
        rules     = get_auto_sms_rules()

        if rules:
            df = pd.DataFrame(rules)
            trigger_labels = {
                "membership_expire": "회원권 만료",
                "birthday": "생일",
                "no_visit": "장기 미방문",
            }
            df["trigger_type"] = df["trigger_type"].map(trigger_labels).fillna(df["trigger_type"])
            show = df[["id","rule_name","trigger_type","days_offset","template_name","is_active"]].copy()
            show.columns = ["ID","규칙명","트리거","D+일수","템플릿","활성"]
            show["활성"] = show["활성"].apply(lambda v: "✅" if v else "❌")
            st.dataframe(show, use_container_width=True, hide_index=True)

        with st.form("auto_sms_form"):
            st.markdown("##### 규칙 추가 / 수정")
            c1, c2 = st.columns([1, 3])
            rule_id   = c1.number_input("ID (수정 시)", min_value=0, step=1, value=0)
            rule_name = c2.text_input("규칙명 *", placeholder="회원권 만료 7일 전 안내")
            c3, c4 = st.columns(2)
            trigger   = c3.selectbox("트리거", ["membership_expire","birthday","no_visit"],
                                      format_func=lambda x: {"membership_expire":"회원권 만료",
                                                              "birthday":"생일","no_visit":"장기 미방문"}[x])
            days_off  = c4.number_input("기준일 대비 일수",
                                         value=-7, min_value=-365, max_value=365,
                                         help="만료일 7일 전: -7, 당일: 0")
            tpl_opts  = {str(t["id"]): t["name"] for t in templates}
            tpl_sel   = st.selectbox("템플릿 *", list(tpl_opts.keys()),
                                     format_func=lambda x: tpl_opts.get(x,"—"))
            rule_active = st.checkbox("활성화", value=True)
            if st.form_submit_button("저장", type="primary", use_container_width=True):
                if not rule_name or not tpl_sel:
                    st.error("규칙명과 템플릿을 선택하세요.")
                else:
                    upsert_auto_sms_rule({
                        "id": int(rule_id) if rule_id else None,
                        "rule_name": rule_name, "trigger_type": trigger,
                        "days_offset": int(days_off), "template_id": int(tpl_sel),
                        "is_active": 1 if rule_active else 0,
                    })
                    st.success("✅ 저장 완료")
                    st.rerun()

        st.divider()
        st.markdown("##### 수동 실행")
        c1, c2 = st.columns(2)
        run_trigger = c1.selectbox("트리거 선택",
                                   ["membership_expire","birthday"],
                                   format_func=lambda x: {"membership_expire":"회원권 만료 알림",
                                                           "birthday":"생일 축하"}[x])
        if c2.button("지금 실행", type="primary", disabled=not is_configured):
            with st.spinner("자동 발송 실행 중..."):
                results = run_auto_sms(branch, run_trigger, name)
            if results:
                ok = sum(1 for r in results if r["status"] == "sent")
                st.success(f"✅ {ok}/{len(results)}명 발송 완료")
            else:
                st.info("발송 대상이 없습니다.")

    # ════════════════════════════════════════
    # 발송 이력
    # ════════════════════════════════════════
    with tab_log:
        st.markdown("#### 문자 발송 이력")
        logs = get_sms_logs(200)
        if not logs:
            st.info("발송 이력이 없습니다.")
        else:
            df = pd.DataFrame(logs)
            show = df[["sent_at","recipient_name","recipient","content","status","sent_by_name","error_msg"]].copy()
            show.columns = ["발송일시","수신자","번호","내용","상태","담당","오류"]
            show["내용"] = show["내용"].str[:30] + "..."
            show["상태"] = show["상태"].map({"sent":"✅ 성공","failed":"❌ 실패","pending":"⏳"}).fillna(show["상태"])
            show["발송일시"] = show["발송일시"].str[:16]
            st.dataframe(show, use_container_width=True, hide_index=True, height=400)

            ok   = sum(1 for l in logs if l["status"]=="sent")
            fail = sum(1 for l in logs if l["status"]=="failed")
            st.caption(f"총 {len(logs)}건 | ✅ 성공 {ok}건 | ❌ 실패 {fail}건")

    # ════════════════════════════════════════
    # Aligo 설정
    # ════════════════════════════════════════
    with tab_cfg:
        st.markdown("#### 알리고 SMS API 설정")
        st.info("""
        **알리고(Aligo) 가입 및 설정**
        1. [알리고 홈페이지](https://smartsms.aligo.in) 회원가입
        2. 발신번호 등록 (사업자 인증 또는 개인 인증)
        3. API 키 발급: 마이페이지 → API 설정

        - **API Key**: 알리고에서 발급받은 키
        - **사용자 ID**: 알리고 로그인 아이디
        - **발신번호**: 등록된 발신번호 (예: 0212345678)
        """)
        with st.form("aligo_cfg_form"):
            api_key = st.text_input("API Key *", value=cfg.get("api_key",""), type="default")
            user_id = st.text_input("사용자 ID *", value=cfg.get("user_id",""))
            sender  = st.text_input("발신번호 *", value=cfg.get("sender",""),
                                    placeholder="01012345678 또는 0212345678")
            if st.form_submit_button("저장", type="primary"):
                if not api_key or not user_id or not sender:
                    st.error("모든 항목을 입력하세요.")
                else:
                    save_aligo_config(api_key.strip(), user_id.strip(), sender.strip())
                    st.success("✅ Aligo 설정 저장 완료")
                    st.rerun()

        if is_configured:
            st.success(f"✅ Aligo 설정 완료 — 발신번호: {cfg['sender']}")

            # 테스트 발송
            st.divider()
            st.markdown("##### 테스트 발송")
            with st.form("aligo_test_form"):
                test_phone = st.text_input("테스트 수신번호", placeholder="010-0000-0000")
                if st.form_submit_button("테스트 발송"):
                    res = aligo_send(test_phone, "[라온스포츠] Aligo 테스트 문자입니다.")
                    if res.get("result_code") == "1":
                        st.success("✅ 테스트 발송 성공!")
                    else:
                        st.error(f"❌ 발송 실패: {res.get('message','')}")
