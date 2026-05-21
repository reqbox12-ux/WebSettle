"""
domains/upload/ui.py — 데이터 업로드 페이지
"""
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from shared.config import BRANCH_LIST, ALL_CATEGORIES
from shared.db import (
    upsert_card_sales, upsert_bank_transactions,
    delete_card_sales, delete_bank_transactions,
)
from shared.utils import sec
from modules.parser import (
    parse_card_aggregate, parse_credit_card,
    parse_bank_auto, recalc_vat,
)
from modules.classifier import classify_transactions
from modules.ai_classifier import ai_classify_batch, load_api_key

_now = datetime.now()


def render_page():
    st.markdown(
        '<div class="ph"><div class="ph-title">데이터 업로드</div>'
        '<div class="ph-sub">엑셀 파일을 업로드하면 자동으로 파싱·저장됩니다</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="al al-info">ℹ️&nbsp; 같은 연월을 다시 올리면 기존 데이터가 교체됩니다. '
        '업로드 전 백업을 권장합니다.</div>',
        unsafe_allow_html=True,
    )

    _api_key = load_api_key()
    tab1, tab2 = st.tabs(["카드 매출", "통장 내역"])

    # ── 카드 매출 ─────────────────────────────────────────
    with tab1:
        st.subheader("카드 매출 업로드")
        c1, c2 = st.columns(2)
        uy = c1.number_input("연도", value=_now.year, min_value=2020, max_value=2030, key="uy")
        um = c2.selectbox("월", list(range(1, 13)), index=_now.month - 1, key="um",
                          format_func=lambda m: f"{m}월")

        sec("① 카드사 결과 집계 조회")
        f1 = st.file_uploader("카드사 결과 집계 조회.xlsx", type=["xlsx"], key="agg")
        if f1 and st.button("저장", key="b_agg"):
            with st.spinner("처리 중..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(f1.read())
                    tp = tmp.name
                try:
                    df = parse_card_aggregate(tp, uy, um)
                    upsert_card_sales(df, "card_aggregate", uy, um)
                    st.cache_data.clear()
                    un = (df.branch == "미매핑").sum()
                    st.success(f"✅ {len(df)}건 저장 완료 (미매핑 {un}건)")
                    if un:
                        st.dataframe(df[df.branch == "미매핑"][["raw_merchant", "total_amount"]])
                except Exception as e:
                    st.error(f"❌ 오류: {e}")
                finally:
                    os.unlink(tp)

        sec("② 신용카드")
        f2 = st.file_uploader("신용카드.xlsx", type=["xlsx"], key="cc")
        if f2 and st.button("저장", key="b_cc"):
            with st.spinner("처리 중..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(f2.read())
                    tp = tmp.name
                try:
                    df = parse_credit_card(tp, uy, um)
                    upsert_card_sales(df, "credit_card", uy, um)
                    st.cache_data.clear()
                    st.success(f"✅ {len(df)}건 저장 완료")
                except Exception as e:
                    st.error(f"❌ 오류: {e}")
                finally:
                    os.unlink(tp)

        # ── 카드 데이터 클리어 ──────────────────────────
        st.divider()
        st.caption("⚠️ 해당 월 카드매출 전체 삭제 (재업로드 또는 초기화 시 사용)")
        cd1, cd2, cd3 = st.columns([1, 1, 2])
        cl_card_y = cd1.number_input("연도", value=_now.year, min_value=2020, max_value=2030,
                                     key="cl_card_y")
        cl_card_m = cd2.selectbox("월", list(range(1, 13)), index=_now.month - 1,
                                   key="cl_card_m", format_func=lambda m: f"{m}월")
        cd3.markdown("<br>", unsafe_allow_html=True)
        if cd3.button("🗑️ 카드매출 데이터 삭제", key="cl_card_btn", use_container_width=True):
            delete_card_sales(int(cl_card_y), int(cl_card_m))
            st.cache_data.clear()
            st.success(f"✅ {cl_card_y}년 {cl_card_m}월 카드매출 데이터 삭제 완료")
            st.rerun()

    # ── 통장 내역 ─────────────────────────────────────────
    with tab2:
        st.subheader("통장 내역 업로드")
        c1, c2 = st.columns(2)
        by = c1.number_input("연도", value=_now.year, min_value=2020, max_value=2030, key="by")
        bm = c2.selectbox("월", list(range(1, 13)), index=_now.month - 1, key="bm",
                          format_func=lambda m: f"{m}월")
        st.caption("💡 하나통장(여러 시트)과 신한통장이 합쳐진 파일을 그대로 업로드하세요.")
        fb = st.file_uploader("통장내역.xlsx", type=["xlsx"], key="bank")

        if fb:
            _xl_check = pd.ExcelFile(fb)
            with st.expander(f"📋 파일 구조 확인 ({len(_xl_check.sheet_names)}개 시트)", expanded=True):
                for _sn in _xl_check.sheet_names:
                    try:
                        _raw   = _xl_check.parse(_sn, header=None, nrows=4, dtype=str)
                        _hrow  = 0
                        for _ri, _row in _raw.iterrows():
                            _vals = [str(v).strip() for v in _row
                                     if pd.notna(v) and str(v).strip() not in ("nan", "")]
                            if "No" in _vals:
                                _hrow = _ri
                                break
                        _headers = [str(v).strip() for v in _raw.iloc[_hrow]
                                    if pd.notna(v) and str(v).strip() not in ("nan", "")]
                        if any("전체선택" in v for v in _headers):
                            _kind = "🟦 신한통장"
                        elif any("의뢰인" in v or "수취인" in v for v in _headers):
                            _kind = "🟩 하나통장"
                        else:
                            _kind = "❓ 미감지"
                        st.markdown(f"**{_sn}** → {_kind}")
                        st.caption("헤더: " + " | ".join(_headers[:10]))
                    except Exception as _e:
                        st.caption(f"{_sn}: 읽기 실패 ({_e})")

        if fb and st.button("저장", type="primary", key="b_bank"):
            with st.spinner("시트 자동 감지 및 분류 중..."):
                xl        = pd.ExcelFile(fb)
                bank_data = parse_bank_auto(xl, by, bm)
                saved     = False
                bank_names = {"hana": "하나통장", "shinhan": "신한통장"}
                for bank, df in bank_data.items():
                    if df.empty:
                        continue
                    try:
                        df = classify_transactions(df, bank)
                        if _api_key:
                            unclf = df[df["needs_review"] == 1]
                            if not unclf.empty:
                                tx_list = unclf[["description", "counterpart", "deposit", "withdrawal"]].to_dict("records")
                                ai_res  = ai_classify_batch(tx_list, BRANCH_LIST, ALL_CATEGORIES, _api_key)
                                for item in ai_res:
                                    try:
                                        loc_idx = unclf.index[item["id"]]
                                        br   = item.get("branch", "")
                                        cat  = item.get("category", "")
                                        conf = float(item.get("confidence", 0))
                                        if br or cat:
                                            df.at[loc_idx, "branch"]   = br
                                            df.at[loc_idx, "category"] = cat
                                            df.at[loc_idx, "classification_source"] = "ai"
                                            df.at[loc_idx, "is_excluded"] = 1 if cat == "제외" else 0
                                            if conf >= 0.75 and br and cat:
                                                df.at[loc_idx, "needs_review"] = 0
                                    except Exception:
                                        pass
                        df    = recalc_vat(df)
                        upsert_bank_transactions(df, bank, by, bm)
                        total    = len(df)
                        auto_ok  = int((df.needs_review == 0).sum())
                        need_rev = int(df.needs_review.sum())
                        ai_cnt   = int((df.get("classification_source", "") == "ai").sum()) if "classification_source" in df.columns else 0
                        st.success(
                            f"✅ {bank_names[bank]}: 총 {total}건 저장 "
                            f"(자동분류 {auto_ok}건 / AI {ai_cnt}건 / 미분류 {need_rev}건)"
                        )
                        saved = True
                    except Exception as e:
                        st.error(f"❌ {bank_names[bank]} 저장 실패: {e}")
                if not saved:
                    st.warning("⚠️ 하나·신한 통장 시트를 찾지 못했습니다.")
                else:
                    if any(not bank_data[b].empty for b in bank_data):
                        need_total = sum(int(df.needs_review.sum())
                                         for df in bank_data.values() if not df.empty)
                        if need_total > 0:
                            st.info(f"📋 미분류 {need_total}건은 '규칙 관리 → 계정과목 검토'에서 확인하세요.")
                    st.cache_data.clear()

        # ── 통장 데이터 클리어 ──────────────────────────
        st.divider()
        st.caption("⚠️ 해당 월 통장내역 삭제 (재업로드 또는 초기화 시 사용)")
        bd1, bd2, bd3, bd4 = st.columns([1, 1, 1, 1])
        cl_bank_y = bd1.number_input("연도", value=_now.year, min_value=2020, max_value=2030,
                                     key="cl_bank_y")
        cl_bank_m = bd2.selectbox("월", list(range(1, 13)), index=_now.month - 1,
                                   key="cl_bank_m", format_func=lambda m: f"{m}월")
        cl_bank_t = bd3.selectbox("통장", ["전체", "하나(hana)", "신한(shinhan)"],
                                   key="cl_bank_t")
        bd4.markdown("<br>", unsafe_allow_html=True)
        if bd4.button("🗑️ 통장내역 삭제", key="cl_bank_btn", use_container_width=True):
            bank_code = None
            if "하나" in cl_bank_t:
                bank_code = "hana"
            elif "신한" in cl_bank_t:
                bank_code = "shinhan"
            delete_bank_transactions(int(cl_bank_y), int(cl_bank_m), bank_code)
            st.cache_data.clear()
            lbl = cl_bank_t if cl_bank_t != "전체" else "전체"
            st.success(f"✅ {cl_bank_y}년 {cl_bank_m}월 통장내역({lbl}) 삭제 완료")
            st.rerun()
