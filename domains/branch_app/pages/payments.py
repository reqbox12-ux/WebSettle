"""Phase 4 — POS + 토스페이먼츠 결제"""
import streamlit as st
import pandas as pd
import uuid
from datetime import date, timedelta
from domains.branch_app.db import (
    get_branch_products, upsert_branch_product,
    get_members, get_membership_products,
    save_transaction, get_sales,
    get_payment_config, save_payment_config,
    toss_confirm_payment, toss_cancel_payment,
)

_PM_LABELS = {"card":"카드","cash":"현금","transfer":"계좌이체","toss":"Toss 온라인"}


def render(user: dict):
    branch = user["branch"]
    name   = user["name"]

    tab_pos, tab_hist, tab_prod, tab_cfg = st.tabs(
        ["💳 POS / 결제", "📋 결제 이력", "📦 상품 관리", "⚙️ Toss 설정"]
    )

    # ════════════════════════════════════════
    # POS
    # ════════════════════════════════════════
    with tab_pos:
        st.markdown("#### POS — 현장 결제")

        products = get_branch_products(branch)
        members  = get_members(branch)
        ms_prods = get_membership_products(branch)

        # 장바구니 세션 관리
        if "cart" not in st.session_state:
            st.session_state["cart"] = []

        cart = st.session_state["cart"]

        # 상품 선택
        st.markdown("##### 상품 / 회원권 선택")
        tab_goods, tab_ms = st.tabs(["상품", "회원권"])

        with tab_goods:
            if not products:
                st.info("등록된 상품이 없습니다. '상품 관리' 탭에서 추가하세요.")
            else:
                cats = sorted(set(p["category"] for p in products))
                for cat in cats:
                    cat_prods = [p for p in products if p["category"] == cat]
                    st.markdown(f"**{cat}**")
                    cols = st.columns(min(4, len(cat_prods)))
                    for i, p in enumerate(cat_prods):
                        with cols[i % 4]:
                            if st.button(f"{p['name']}\n{p['price']:,}원",
                                         key=f"add_prod_{p['id']}", use_container_width=True):
                                cart.append({
                                    "item_name": p["name"], "unit_price": p["price"],
                                    "quantity": 1, "total_price": p["price"],
                                    "product_id": p["id"],
                                })
                                st.session_state["cart"] = cart
                                st.rerun()

        with tab_ms:
            if not ms_prods:
                st.info("등록된 회원권 상품이 없습니다.")
            else:
                for p in ms_prods:
                    if st.button(f"{p['name']} — {p['price']:,}원 ({p['duration_days']}일)",
                                 key=f"add_ms_{p['id']}", use_container_width=True):
                        cart.append({
                            "item_name": f"[회원권] {p['name']}", "unit_price": p["price"],
                            "quantity": 1, "total_price": p["price"],
                            "product_id": None,
                        })
                        st.session_state["cart"] = cart
                        st.rerun()

        st.divider()

        # 장바구니
        st.markdown("##### 🛒 장바구니")
        if not cart:
            st.info("선택된 상품이 없습니다.")
        else:
            total = 0
            for i, item in enumerate(cart):
                c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 1])
                c1.markdown(f"**{item['item_name']}**")
                new_qty = c2.number_input("수량", min_value=1, value=item["quantity"],
                                          key=f"cart_qty_{i}", label_visibility="collapsed")
                cart[i]["quantity"]    = new_qty
                cart[i]["total_price"] = item["unit_price"] * new_qty
                c3.markdown(f"{item['unit_price']:,}원")
                c4.markdown(f"**{cart[i]['total_price']:,}원**")
                if c5.button("✕", key=f"rm_{i}"):
                    cart.pop(i)
                    st.session_state["cart"] = cart
                    st.rerun()
                total += cart[i]["total_price"]

            st.markdown(f"### 합계: **{total:,}원**")
            st.session_state["cart"] = cart

            st.divider()
            st.markdown("##### 결제 처리")
            with st.form("payment_form"):
                c1, c2, c3 = st.columns([3, 2, 2])
                pay_method = c1.selectbox("결제 수단",
                                          ["card","cash","transfer","toss"],
                                          format_func=lambda x: _PM_LABELS[x])
                mem_opts   = {"": "비회원"} | {str(m["id"]): f"{m['name']} ({m['phone'] or '—'})" for m in members}
                mem_sel    = c2.selectbox("회원 연결 (선택)", list(mem_opts.keys()),
                                          format_func=lambda x: mem_opts[x])
                pay_note   = c3.text_input("메모")

                if pay_method == "toss":
                    st.info("💡 Toss 온라인 결제: 고객 기기에서 결제 후 아래에 결제키를 입력하세요.")
                    toss_order_id  = st.text_input("Toss 주문번호 (자동생성)", value=f"RAON-{uuid.uuid4().hex[:8].upper()}")
                    toss_pay_key   = st.text_input("Toss 결제키 (결제 완료 후 입력)")
                else:
                    toss_order_id = ""
                    toss_pay_key  = ""

                submitted = st.form_submit_button("결제 완료", type="primary", use_container_width=True)

                if submitted:
                    # Toss 온라인 승인
                    confirmed = True
                    if pay_method == "toss" and toss_pay_key:
                        result = toss_confirm_payment(toss_pay_key, toss_order_id, total)
                        if result.get("status") != "DONE":
                            st.error(f"Toss 결제 승인 실패: {result.get('message','알 수 없는 오류')}")
                            confirmed = False
                    elif pay_method == "toss" and not toss_pay_key:
                        st.error("Toss 결제키를 입력하세요.")
                        confirmed = False

                    if confirmed:
                        mem_id   = int(mem_sel) if mem_sel else None
                        mem_name = mem_opts.get(mem_sel, "비회원") if mem_sel else "비회원"
                        save_transaction(
                            branch, cart, pay_method, mem_name, name, pay_note,
                            toss_order_id, toss_pay_key,
                        )
                        st.session_state["cart"] = []
                        st.success(f"✅ 결제 완료! {total:,}원 ({_PM_LABELS[pay_method]})")
                        st.balloons()
                        st.rerun()

            if st.button("🗑 장바구니 비우기", key="clear_cart"):
                st.session_state["cart"] = []
                st.rerun()

    # ════════════════════════════════════════
    # 결제 이력
    # ════════════════════════════════════════
    with tab_hist:
        st.markdown("#### 결제 이력")
        c1, c2, c3 = st.columns([2, 2, 2])
        from_date = c1.text_input("시작일", value=(date.today() - timedelta(days=30)).strftime("%Y-%m-%d"))
        to_date   = c2.text_input("종료일", value=date.today().strftime("%Y-%m-%d"))
        pm_filter = c3.selectbox("결제수단", ["전체","card","cash","transfer","toss"],
                                  format_func=lambda x: "전체" if x=="전체" else _PM_LABELS.get(x,x))

        txs = get_sales(branch, from_date, to_date)
        if pm_filter != "전체":
            txs = [t for t in txs if t["payment_method"] == pm_filter]

        if not txs:
            st.info("결제 내역이 없습니다.")
        else:
            total_amt = sum(t["total_amount"] for t in txs)
            st.markdown(f"**기간 합계: {total_amt:,}원** ({len(txs)}건)")

            df = pd.DataFrame(txs)
            show = df[["paid_at","member_name","total_amount","payment_method",
                        "employee_name","note"]].copy()
            show.columns = ["결제일시","회원","금액","결제수단","담당","메모"]
            show["금액"] = show["금액"].apply(lambda v: f"{int(v):,}원")
            show["결제수단"] = show["결제수단"].map(_PM_LABELS).fillna(show["결제수단"])
            show["결제일시"] = show["결제일시"].str[:16]
            st.dataframe(show, use_container_width=True, hide_index=True, height=400)

            # 취소 처리
            st.divider()
            st.markdown("##### 결제 취소 (Toss)")
            with st.form("cancel_form"):
                cancel_key    = st.text_input("취소할 Toss 결제키")
                cancel_reason = st.text_input("취소 사유", value="고객 요청")
                if st.form_submit_button("결제 취소 요청"):
                    if not cancel_key:
                        st.error("결제키를 입력하세요.")
                    else:
                        res = toss_cancel_payment(cancel_key, cancel_reason)
                        if res.get("error"):
                            st.error(f"취소 실패: {res['error']}")
                        else:
                            st.success("✅ 취소 요청 완료")

    # ════════════════════════════════════════
    # 상품 관리
    # ════════════════════════════════════════
    with tab_prod:
        st.markdown("#### 지점 상품 관리")
        products = get_branch_products(branch, active_only=False)
        if products:
            df = pd.DataFrame(products)
            show = df[["id","name","category","price","stock","is_active"]].copy()
            show.columns = ["ID","상품명","분류","가격","재고","활성"]
            show["가격"] = show["가격"].apply(lambda v: f"{int(v):,}원")
            show["활성"] = show["활성"].apply(lambda v: "✅" if v else "❌")
            st.dataframe(show, use_container_width=True, hide_index=True)

        st.divider()
        with st.form("prod_form"):
            st.markdown("##### 상품 추가 / 수정")
            c1, c2 = st.columns([1, 3])
            prod_id   = c1.number_input("ID (수정 시)", min_value=0, step=1, value=0)
            prod_name = c2.text_input("상품명 *")
            c3, c4, c5, c6 = st.columns(4)
            prod_cat   = c3.text_input("분류", value="기타")
            prod_price = c4.number_input("가격(원)", min_value=0, step=100)
            prod_stock = c5.number_input("재고", min_value=0, value=0)
            prod_act   = c6.checkbox("활성", value=True)
            if st.form_submit_button("저장", type="primary", use_container_width=True):
                if not prod_name:
                    st.error("상품명을 입력하세요.")
                else:
                    upsert_branch_product({
                        "id": int(prod_id) if prod_id else None,
                        "branch": branch, "name": prod_name, "category": prod_cat,
                        "price": int(prod_price), "stock": int(prod_stock),
                        "is_active": 1 if prod_act else 0,
                    })
                    st.success("✅ 저장 완료")
                    st.rerun()

    # ════════════════════════════════════════
    # Toss 설정
    # ════════════════════════════════════════
    with tab_cfg:
        st.markdown("#### 토스페이먼츠 API 설정")
        st.info("""
        **Toss Payments 연동 방법**
        1. [토스페이먼츠 개발자센터](https://developers.tosspayments.com) 가입 후 상점 등록
        2. 테스트 키 발급 → 개발/테스트 진행
        3. 실결제 승인 후 실제 키로 교체

        - **클라이언트 키**: 프론트엔드 결제창 호출 시 사용 (공개 가능)
        - **시크릿 키**: 서버사이드 결제 승인/취소 시 사용 (절대 비공개)
        """)
        cfg = get_payment_config()
        with st.form("toss_cfg_form"):
            client_key = st.text_input("클라이언트 키 (test_ck_... 또는 live_ck_...)",
                                       value=cfg.get("toss_client_key",""), type="default")
            secret_key = st.text_input("시크릿 키 (test_sk_... 또는 live_sk_...)",
                                       value=cfg.get("toss_secret_key",""), type="password")
            if st.form_submit_button("저장", type="primary"):
                save_payment_config(client_key.strip(), secret_key.strip())
                st.success("✅ Toss API 키 저장 완료")

        if cfg.get("toss_client_key"):
            st.success(f"✅ Toss 클라이언트 키 등록됨: {cfg['toss_client_key'][:20]}...")
        else:
            st.warning("⚠️ Toss API 키가 설정되지 않았습니다.")

        st.markdown("""
        #### Toss 결제 흐름
        ```
        [POS에서 금액 입력] → [Toss 결제 링크 공유/QR]
            ↓ 고객이 결제 완료
        [결제키(paymentKey) 발급]
            ↓
        [POS에서 결제키 입력 → 승인 API 호출]
            ↓
        [결제 완료 기록]
        ```
        > 현재는 수동 결제키 입력 방식입니다.
        > 자동화를 원하시면 Toss 결제위젯 연동이 필요합니다.
        """)
