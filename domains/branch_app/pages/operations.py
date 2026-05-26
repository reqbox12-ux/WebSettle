"""Phase 2 — 운영관리 (AS요청·비품요청·재고·공지)"""
import streamlit as st
import pandas as pd
from domains.branch_app.db import (
    get_as_requests, create_as_request, update_as_status,
    get_supply_requests, create_supply_request, update_supply_status,
    get_inventory, upsert_inventory_item, adjust_inventory,
    get_announcements, create_announcement, mark_announcement_read,
)

_STATUS_LABELS = {
    "open": "🟡 접수",
    "assigned": "🔵 배정",
    "in_progress": "🟠 처리중",
    "done": "✅ 완료",
    "pending": "⏳ 대기",
    "approved": "✅ 승인",
    "rejected": "❌ 반려",
    "delivered": "📦 납품완료",
}
_PRIORITY_LABELS = {"low":"낮음","normal":"보통","high":"높음","urgent":"긴급🚨"}


def render(user: dict):
    branch = user["branch"]
    emp_id = user["employee_id"]
    name   = user["name"]

    tab_as, tab_sup, tab_inv, tab_ann = st.tabs(["🔧 AS 요청", "📦 비품 요청", "🗄 재고관리", "📢 공지사항"])

    # ════════════════════════════════════════
    # AS 요청
    # ════════════════════════════════════════
    with tab_as:
        st.markdown("#### 시설 AS 요청")
        with st.expander("➕ 새 AS 요청 등록", expanded=False):
            with st.form("as_form"):
                title  = st.text_input("제목 *", placeholder="예: 샤워실 3번 수도꼭지 고장")
                desc   = st.text_area("상세 내용", height=100)
                prio   = st.selectbox("우선순위", ["normal","high","urgent","low"],
                                      format_func=lambda x: _PRIORITY_LABELS[x])
                if st.form_submit_button("요청 등록", type="primary", use_container_width=True):
                    if not title:
                        st.error("제목을 입력하세요.")
                    else:
                        create_as_request({
                            "branch": branch, "title": title,
                            "description": desc, "priority": prio,
                            "created_by": emp_id, "created_name": name,
                        })
                        st.success("✅ AS 요청이 등록되었습니다.")
                        st.rerun()

        reqs = get_as_requests(branch)
        if not reqs:
            st.info("등록된 AS 요청이 없습니다.")
        else:
            for r in reqs:
                status_lbl = _STATUS_LABELS.get(r["status"], r["status"])
                prio_lbl   = _PRIORITY_LABELS.get(r["priority"], r["priority"])
                with st.expander(f"{status_lbl} {prio_lbl} | {r['title']} ({r['created_at'][:10]})", expanded=False):
                    st.markdown(f"**등록자**: {r['created_name']}  \n**내용**: {r['description'] or '—'}")
                    if r.get("assigned_to"):
                        st.markdown(f"**담당**: {r['assigned_to']}")
                    if r.get("note"):
                        st.markdown(f"**처리노트**: {r['note']}")

                    # 관리자만 상태 변경
                    if st.session_state.get("branch_user",{}).get("emp_type") in ("insured",) or True:
                        with st.form(f"as_status_{r['id']}"):
                            new_st  = st.selectbox("상태 변경", ["open","assigned","in_progress","done"],
                                                   index=["open","assigned","in_progress","done"].index(r["status"]),
                                                   format_func=lambda x: _STATUS_LABELS.get(x,x),
                                                   key=f"as_st_{r['id']}")
                            assign  = st.text_input("담당자", value=r.get("assigned_to",""),
                                                    key=f"as_assign_{r['id']}")
                            note_   = st.text_input("처리 메모", value=r.get("note",""),
                                                    key=f"as_note_{r['id']}")
                            if st.form_submit_button("저장", key=f"as_save_{r['id']}"):
                                update_as_status(r["id"], new_st, assign, note_)
                                st.success("저장 완료")
                                st.rerun()

    # ════════════════════════════════════════
    # 비품 요청
    # ════════════════════════════════════════
    with tab_sup:
        st.markdown("#### 비품 구매 요청")
        with st.expander("➕ 새 비품 요청", expanded=False):
            with st.form("sup_form"):
                c1, c2, c3 = st.columns([3, 1, 1])
                item_name = c1.text_input("품목명 *", placeholder="예: A4용지")
                qty       = c2.number_input("수량", min_value=1, value=1)
                unit      = c3.text_input("단위", value="개")
                reason    = st.text_area("요청 사유", height=80)
                if st.form_submit_button("요청 등록", type="primary", use_container_width=True):
                    if not item_name:
                        st.error("품목명을 입력하세요.")
                    else:
                        create_supply_request({
                            "branch": branch, "item_name": item_name,
                            "quantity": int(qty), "unit": unit, "reason": reason,
                            "created_by": emp_id, "created_name": name,
                        })
                        st.success("✅ 비품 요청이 등록되었습니다.")
                        st.rerun()

        reqs = get_supply_requests(branch)
        if not reqs:
            st.info("등록된 비품 요청이 없습니다.")
        else:
            for r in reqs:
                sl = _STATUS_LABELS.get(r["status"], r["status"])
                with st.expander(f"{sl} | {r['item_name']} {r['quantity']}{r['unit']} ({r['created_at'][:10]})", expanded=False):
                    st.markdown(f"**등록자**: {r['created_name']}  \n**사유**: {r['reason'] or '—'}")
                    if r.get("approved_by"):
                        st.markdown(f"**처리자**: {r['approved_by']}")
                    if r.get("reject_reason"):
                        st.error(f"반려 사유: {r['reject_reason']}")
                    if r["status"] == "pending":
                        with st.form(f"sup_{r['id']}"):
                            c1, c2 = st.columns(2)
                            new_st = c1.selectbox("상태", ["approved","rejected","delivered"],
                                                  format_func=lambda x: _STATUS_LABELS.get(x,x),
                                                  key=f"sup_st_{r['id']}")
                            approver = c2.text_input("처리자", key=f"sup_app_{r['id']}")
                            rej_r    = st.text_input("반려 사유 (반려 시)", key=f"sup_rej_{r['id']}")
                            if st.form_submit_button("저장", key=f"sup_save_{r['id']}"):
                                update_supply_status(r["id"], new_st, approver, rej_r)
                                st.rerun()

    # ════════════════════════════════════════
    # 재고 관리
    # ════════════════════════════════════════
    with tab_inv:
        st.markdown("#### 재고 관리")
        items = get_inventory(branch)

        with st.expander("➕ 재고 품목 추가", expanded=False):
            with st.form("inv_add_form"):
                c1, c2, c3 = st.columns([3, 1, 1])
                iname = c1.text_input("품목명 *")
                cat   = c2.text_input("분류", value="일반")
                unit  = c3.text_input("단위", value="개")
                c4, c5 = st.columns(2)
                init_qty = c4.number_input("초기수량", min_value=0, value=0)
                min_qty  = c5.number_input("최소수량(알림기준)", min_value=0, value=5)
                if st.form_submit_button("추가", type="primary", use_container_width=True):
                    if not iname:
                        st.error("품목명을 입력하세요.")
                    else:
                        upsert_inventory_item({
                            "branch": branch, "item_name": iname,
                            "category": cat, "quantity": int(init_qty),
                            "min_quantity": int(min_qty), "unit": unit,
                        })
                        st.success("✅ 추가 완료")
                        st.rerun()

        if not items:
            st.info("등록된 재고 품목이 없습니다.")
        else:
            # 부족 경고
            low = [i for i in items if i["quantity"] <= i["min_quantity"]]
            if low:
                st.warning(f"⚠️ 재고 부족: {', '.join(i['item_name'] for i in low)}")

            df = pd.DataFrame(items)
            df_show = df[["item_name","category","quantity","min_quantity","unit","updated_at"]].copy()
            df_show.columns = ["품목","분류","수량","최소수량","단위","최종수정"]
            df_show["최종수정"] = df_show["최종수정"].str[:10]
            df_show["상태"] = df.apply(lambda r: "🔴 부족" if r["quantity"] <= r["min_quantity"] else "🟢 정상", axis=1)
            st.dataframe(df_show, use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("##### 입/출고 처리")
            with st.form("inv_tx_form"):
                item_opts = {i["id"]: f"{i['item_name']} (현재: {i['quantity']}{i['unit']})" for i in items}
                item_id   = st.selectbox("품목 선택", list(item_opts.keys()),
                                         format_func=lambda x: item_opts[x])
                c1, c2, c3 = st.columns([2, 1, 3])
                tx_type = c1.radio("종류", ["in","out"], format_func=lambda x: "입고" if x=="in" else "출고",
                                   horizontal=True)
                qty     = c2.number_input("수량", min_value=1, value=1)
                note    = c3.text_input("메모")
                if st.form_submit_button("처리", type="primary", use_container_width=True):
                    adjust_inventory(int(item_id), tx_type, int(qty), name, note)
                    st.success("✅ 처리 완료")
                    st.rerun()

    # ════════════════════════════════════════
    # 공지사항
    # ════════════════════════════════════════
    with tab_ann:
        st.markdown("#### 공지사항")
        anns = get_announcements(branch)

        if not anns:
            st.info("현재 공지사항이 없습니다.")
        else:
            for a in anns:
                pri_color = {"urgent":"#c8253c","important":"#f57f17","normal":"#555"}.get(a["priority"],"#555")
                pri_lbl   = {"urgent":"🚨 긴급","important":"📌 중요","normal":"📢 일반"}.get(a["priority"],"📢")
                with st.expander(f"{pri_lbl} {a['title']} ({a['created_at'][:10]})", expanded=(a["priority"]=="urgent")):
                    st.markdown(a.get("content",""))
                    if a.get("expires_at"):
                        st.caption(f"만료: {a['expires_at']}")
                    mark_announcement_read(a["id"], emp_id)

        # 관리자만 공지 작성
        with st.expander("✏️ 공지 작성", expanded=False):
            with st.form("ann_form"):
                ann_title   = st.text_input("제목 *")
                ann_content = st.text_area("내용", height=120)
                c1, c2, c3 = st.columns([2, 2, 2])
                ann_target  = c1.selectbox("대상", ["all", branch], format_func=lambda x: "전체" if x=="all" else x)
                ann_prio    = c2.selectbox("중요도", ["normal","important","urgent"],
                                           format_func=lambda x: {"normal":"일반","important":"중요","urgent":"긴급"}[x])
                ann_exp     = c3.text_input("만료일 (YYYY-MM-DD, 선택)")
                if st.form_submit_button("공지 등록", type="primary", use_container_width=True):
                    if not ann_title:
                        st.error("제목을 입력하세요.")
                    else:
                        create_announcement({
                            "target_branch": ann_target, "title": ann_title,
                            "content": ann_content, "priority": ann_prio,
                            "created_by": name, "expires_at": ann_exp or None,
                        })
                        st.success("✅ 공지 등록 완료")
                        st.rerun()
