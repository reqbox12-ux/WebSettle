"""
domains/branch/ui.py — 지점 상세 페이지 (전월 대비 + 손익계산서 통합 뷰)
"""
import base64
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from shared.config import BRANCH_LIST as _JSON_BRANCH_LIST
from shared.utils import fn, fw, sec, PLOT_BASE
from domains.dashboard.service import build_summary, c_rev, c_exp
from domains.branch.db import (
    get_active_branch_names, get_all_branches, upsert_branch,
    get_branch_monthly_revenue, upsert_branch_monthly_revenue,
)

_now = datetime.now()

# ── 유틸 ─────────────────────────────────────────────────────
def _prev_ym(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _delta_badge(curr: float, prev: float) -> str:
    if prev == 0:
        return '<span style="font-size:11px;color:var(--ink3)">—</span>'
    diff = curr - prev
    pct  = diff / abs(prev) * 100
    sign = "▲" if diff >= 0 else "▼"
    col  = "var(--pos)" if diff >= 0 else "var(--red)"
    bg   = "var(--poss)" if diff >= 0 else "var(--reds)"
    return (
        f'<span style="display:inline-flex;align-items:center;gap:3px;'
        f'padding:2px 8px;border-radius:999px;background:{bg};'
        f'color:{col};font-size:11px;font-weight:700">'
        f'{sign} {abs(pct):.1f}%</span>'
    )


# ── 전월 대비 KPI 카드 ────────────────────────────────────────
def _render_mom_kpi(curr: dict, prev: dict):
    items = [
        ("총 매출",   curr["총매출"],       prev["총매출"],       "c-ink"),
        ("카드 실수령", curr["카드실수령"],   prev["카드실수령"],   "c-ink"),
        ("현금 매출", curr["현금공급가액"],  prev["현금공급가액"], "c-ink"),
        ("총 지출",   curr["총지출"],        prev["총지출"],        "c-red"),
        ("순 손익",   curr["손익"],          prev["손익"],
         "c-pos" if curr["손익"] >= 0 else "c-red"),
    ]
    html = '<div class="kpi-grid">'
    for lbl, c_val, p_val, cls in items:
        delta = _delta_badge(c_val, p_val)
        html += (
            f'<div class="kpi">'
            f'<div class="kpi-lbl">{lbl}</div>'
            f'<div class="kpi-val {cls}">{fw(abs(int(c_val)))}'
            f'<span class="kpi-unit">원</span></div>'
            f'<div class="kpi-sub" style="display:flex;align-items:center;gap:6px">'
            f'전월 {fw(abs(int(p_val)))} &nbsp;{delta}</div>'
            f'</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── 전월 대비 비교 차트 ──────────────────────────────────────
def _render_mom_chart(curr: dict, prev: dict, year: int, month: int, key: str):
    p_year, p_month = _prev_ym(year, month)
    labels   = ["총 매출", "총 지출", "순 손익"]
    c_vals   = [curr["총매출"], curr["총지출"], curr["손익"]]
    p_vals   = [prev["총매출"], prev["총지출"], prev["손익"]]

    bar_colors_c = ["#3D3835", "#E60028", "#2E7D5B" if curr["손익"] >= 0 else "#E60028"]
    bar_colors_p = ["rgba(61,56,53,.35)", "rgba(230,0,40,.35)",
                    "rgba(46,125,91,.35)" if prev["손익"] >= 0 else "rgba(230,0,40,.35)"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=f"{year}년 {month}월 (이번달)",
        x=labels, y=c_vals,
        marker_color=bar_colors_c,
        text=[fw(abs(int(v))) for v in c_vals],
        textposition="outside",
        textfont=dict(size=11),
    ))
    fig.add_trace(go.Bar(
        name=f"{p_year}년 {p_month}월 (전월)",
        x=labels, y=p_vals,
        marker_color=bar_colors_p,
        text=[fw(abs(int(v))) for v in p_vals],
        textposition="outside",
        textfont=dict(size=11, color="#9A918C"),
    ))
    fig.update_layout(**{
        **PLOT_BASE,
        "barmode": "group",
        "height": 340,
        "margin": dict(t=30, b=20, l=10, r=10),
        "yaxis": dict(tickformat=",", gridcolor="rgba(31,27,27,.07)", zeroline=True,
                      zerolinecolor="rgba(31,27,27,.15)"),
        "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                       font=dict(size=11)),
        "bargap": 0.25, "bargroupgap": 0.1,
    })
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── 손익계산서 통합 패널 ─────────────────────────────────────
def _render_pnl_panel(row: dict, year: int, month: int):
    b = row["branch"]

    rev_df = c_rev(year, month)
    rev_by_cat: dict = {}
    if not rev_df.empty:
        br_rev = rev_df[rev_df.branch == b]
        rev_by_cat = br_rev.set_index("category")["supply_amount"].to_dict()

    exp_df = c_exp(year, month)
    exp_by_cat: dict = {}
    if not exp_df.empty:
        br_exp = exp_df[exp_df.branch == b]
        exp_by_cat = br_exp.groupby("category")["amount"].sum().to_dict()

    CARD_CATS = ["PT매출(카드)", "GX매출(카드)", "골프매출(카드)", "키즈매출(카드)", "기타매출(카드)"]
    CASH_CATS = ["PT매출(현금)", "GX매출(현금)", "골프매출(현금)", "키즈매출(현금)", "기타매출(현금)",
                 "도급비", "시설상환비", "카페매출"]

    def _row(lbl, amt, indent=False, bold=False, cls=""):
        style_lbl = "color:var(--ink3);padding-left:20px" if indent else "color:var(--ink);font-weight:600" if bold else "color:var(--ink2)"
        style_amt = f"font-feature-settings:'tnum' 1;font-weight:{'700' if bold else '500'};{f'color:{cls}' if cls else ''}"
        border    = "border-top:2px solid var(--bds);margin-top:4px;padding-top:10px" if bold else "border-bottom:1px solid var(--bd)"
        return (
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:{"10px" if bold else "6px"} 0;{border}">'
            f'<span style="font-size:{"14px" if bold else "12.5px"};{style_lbl}">{lbl}</span>'
            f'<span style="font-size:{"14px" if bold else "12.5px"};{style_amt}">{fn(int(amt))}원</span>'
            f'</div>'
        )

    # 수익 섹션
    rev_html = '<div style="font-size:10px;font-weight:700;color:var(--ink3);letter-spacing:.07em;text-transform:uppercase;padding-bottom:8px;border-bottom:1px solid var(--bd);margin-bottom:2px">수 익</div>'
    for cat in CARD_CATS:
        v = int(rev_by_cat.get(cat, 0))
        if v > 0:
            rev_html += _row(cat, v, indent=True)
    if int(row.get("카드수수료", 0)) > 0:
        rev_html += _row(f"카드수수료 차감", -int(row["카드수수료"]), indent=True)
    rev_html += _row("카드 실수령", row["카드실수령"], bold=True)

    for cat in CASH_CATS:
        v = int(rev_by_cat.get(cat, 0))
        if v > 0:
            rev_html += _row(cat, v, indent=True)
    if int(row.get("현금VAT", 0)) > 0:
        rev_html += _row("부가세 차감", -int(row["현금VAT"]), indent=True)
    rev_html += _row("현금 공급가액", row["현금공급가액"], bold=True)

    # 총매출 합계
    rev_html += (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:12px 0;border-top:2px solid var(--ink);margin-top:6px">'
        f'<span style="font-size:15px;font-weight:800;color:var(--ink)">총 매출</span>'
        f'<span style="font-size:15px;font-weight:800;color:var(--ink);font-feature-settings:\'tnum\' 1">'
        f'{fn(int(row["총매출"]))}원</span></div>'
    )

    # 비용 섹션
    exp_html = '<div style="font-size:10px;font-weight:700;color:var(--ink3);letter-spacing:.07em;text-transform:uppercase;padding-bottom:8px;border-bottom:1px solid var(--bd);margin-bottom:2px;margin-top:8px">비 용</div>'
    PAY_ITEMS = [
        ("급여 (실수령)",        "급여"),
        ("4대보험료 (직원부담)", "4대보험료_직원"),
        ("4대보험료 (본사부담)", "4대보험_본사"),
        ("소득세·지방세",        "소득세지방세"),
        ("프리랜서",             "프리랜서"),
        ("프리랜서 세금",        "프리랜서세금"),
    ]
    for lbl, key in PAY_ITEMS:
        v = int(row.get(key, 0))
        if v > 0:
            exp_html += _row(lbl, v, indent=True)
    exp_html += _row("인건비 합계", row["인건비합계"], bold=True)

    for cat, amt in sorted(exp_by_cat.items(), key=lambda x: -x[1]):
        if amt > 0:
            exp_html += _row(cat, int(amt), indent=True)
    if int(row.get("기타지출", 0)) > 0:
        exp_html += _row("기타지출 합계", row["기타지출"], bold=True)

    if int(row.get("부가세합계", 0)) > 0:
        exp_html += _row("부가세 합계", row["부가세합계"], bold=True)

    # 총지출 합계
    exp_html += (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:12px 0;border-top:2px solid var(--ink);margin-top:6px">'
        f'<span style="font-size:15px;font-weight:800;color:var(--red)">총 지출</span>'
        f'<span style="font-size:15px;font-weight:800;color:var(--red);font-feature-settings:\'tnum\' 1">'
        f'{fn(int(row["총지출"]))}원</span></div>'
    )

    pnl     = int(row["손익"])
    rate    = row["이익률"]
    pnl_col = "var(--pos)" if pnl >= 0 else "var(--red)"
    sign    = "▲" if pnl >= 0 else "▼"

    pnl_html = (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:16px 20px;background:{"var(--poss)" if pnl >= 0 else "var(--reds)"};'
        f'border-radius:var(--rs);margin-top:16px">'
        f'<span style="font-size:16px;font-weight:800;color:{pnl_col}">순 손익</span>'
        f'<div style="text-align:right">'
        f'<div style="font-size:20px;font-weight:800;color:{pnl_col};font-feature-settings:\'tnum\' 1">'
        f'{sign} {fn(abs(pnl))}원</div>'
        f'<div style="font-size:13px;font-weight:600;color:{pnl_col}">'
        f'{"+" if rate >= 0 else ""}{rate:.1f}%</div>'
        f'</div></div>'
    )

    st.markdown(
        f'<div style="background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);'
        f'padding:24px;box-shadow:var(--shm)">'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:32px">'
        f'<div>{rev_html}</div>'
        f'<div>{exp_html}</div>'
        f'</div>'
        f'{pnl_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── 연간 월별 추이 차트 ──────────────────────────────────────
def _render_yearly_trend(br_sel: str, year: int, month: int):
    months_data = []
    for m in range(1, 13):
        r     = build_summary(year, m)
        row_m = r[r.branch == br_sel]
        if not row_m.empty:
            months_data.append({
                "월": f"{m}월",
                "총매출": row_m.iloc[0]["총매출"],
                "총지출": row_m.iloc[0]["총지출"],
                "손익":   row_m.iloc[0]["손익"],
            })
        else:
            months_data.append({"월": f"{m}월", "총매출": 0, "총지출": 0, "손익": 0})

    import pandas as pd
    mdf = pd.DataFrame(months_data)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="총매출", x=mdf["월"], y=mdf["총매출"],
        marker_color="#3D3835", opacity=0.8,
    ))
    fig.add_trace(go.Bar(
        name="총지출", x=mdf["월"], y=mdf["총지출"],
        marker_color="#E60028", opacity=0.72,
    ))
    fig.add_trace(go.Scatter(
        name="손익", x=mdf["월"], y=mdf["손익"],
        mode="lines+markers", yaxis="y2",
        line=dict(color="#2E7D5B", width=2.5),
        marker=dict(
            size=8,
            color=["#2E7D5B" if v >= 0 else "#E60028" for v in mdf["손익"]],
            line=dict(width=2, color="white"),
        ),
    ))
    # 현재 월 강조
    fig.add_vline(
        x=f"{month}월", line_width=1.5, line_dash="dot",
        line_color="rgba(230,0,40,.4)",
    )
    fig.update_layout(**{
        **PLOT_BASE,
        "barmode": "group",
        "height": 300,
        "margin": dict(t=16, b=20, l=10, r=10),
        "yaxis":  dict(tickformat=",", gridcolor="rgba(31,27,27,.07)", zeroline=False),
        "yaxis2": dict(overlaying="y", side="right", tickformat=",",
                       zeroline=True, zerolinecolor="rgba(31,27,27,.2)"),
        "xaxis":  dict(tickfont=dict(size=11)),
    })
    st.plotly_chart(fig, use_container_width=True)


# ── 지점 페이지 메인 ─────────────────────────────────────────
def render_page():
    year  = st.session_state.year
    month = st.session_state.month

    st.markdown(
        '<div class="ph"><div class="ph-title">지점 상세 내역</div>'
        '<div class="ph-sub">지점 상세 분석 · 지점 관리 · 월별 매출 직접 입력</div></div>',
        unsafe_allow_html=True,
    )

    tab_detail, tab_mgmt, tab_revenue = st.tabs(["📊 지점 상세", "🏢 지점 관리", "📝 월별 매출 입력"])

    with tab_detail:
        _render_detail(year, month)

    with tab_mgmt:
        _render_branch_mgmt()

    with tab_revenue:
        _render_monthly_revenue(year, month)


def _render_detail(year: int, month: int):
    """기존 지점 상세 뷰 (전월 대비 + 손익계산서 + 추이 + PDF)"""
    BRANCH_LIST = get_active_branch_names()

    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns([1, 1, 2])
    yrs    = list(range(_now.year, _now.year - 3, -1))
    year   = fc1.selectbox("연도", yrs, index=yrs.index(year) if year in yrs else 0, key="br_yr")
    month  = fc2.selectbox("월", list(range(1, 13)), index=month - 1, key="br_mn",
                            format_func=lambda m: f"{m}월")
    br_sel = fc3.selectbox("지점 선택", BRANCH_LIST, key="br_sel")
    st.session_state.year  = year
    st.session_state.month = month
    st.markdown('</div>', unsafe_allow_html=True)

    with st.spinner("데이터 로드 중..."):
        full_df  = build_summary(year, month)
        p_year, p_month = _prev_ym(year, month)
        prev_df  = build_summary(p_year, p_month)

    br_row   = full_df[full_df.branch == br_sel]
    prev_row = prev_df[prev_df.branch == br_sel]

    has_data = (not br_row.empty and
                (br_row.iloc[0]["총매출"] != 0 or br_row.iloc[0]["총지출"] != 0))

    if not has_data:
        _rev_check = c_rev(year, month)
        _exp_check = c_exp(year, month)
        _has = ((not _rev_check.empty and br_sel in _rev_check.branch.values) or
                (not _exp_check.empty and br_sel in _exp_check.branch.values))
        if not _has:
            st.markdown('<div class="al al-warn">⚠️&nbsp; 해당 지점의 데이터가 없습니다.</div>',
                        unsafe_allow_html=True)
            return

    def _empty_row(branch: str) -> dict:
        r = {c: 0 for c in full_df.columns}
        r["branch"] = branch
        r["이익률"] = 0.0
        return r

    curr_d = br_row.iloc[0].to_dict() if not br_row.empty else _empty_row(br_sel)
    prev_d = prev_row.iloc[0].to_dict() if not prev_row.empty else _empty_row(br_sel)

    # ── 전월 대비 KPI 카드
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'margin-bottom:16px">'
        f'<div style="font-size:13px;font-weight:600;color:var(--ink)">'
        f'{year}년 {month}월 &nbsp;·&nbsp; {br_sel}</div>'
        f'<div style="font-size:11px;color:var(--ink3)">전월({p_year}년 {p_month}월) 대비</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    _render_mom_kpi(curr_d, prev_d)

    # ── 전월 대비 비교 차트
    st.markdown(
        f'<div class="ch"><div class="ch-t">전월 대비 비교 — {br_sel}</div>'
        f'<div class="ch-s">{year}년 {month}월 vs {p_year}년 {p_month}월</div>',
        unsafe_allow_html=True,
    )
    _render_mom_chart(curr_d, prev_d, year, month, key="mom_chart")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 손익계산서
    sec("손익계산서")
    _render_pnl_panel(curr_d, year, month)

    # ── 연간 월별 추이
    sec(f"{year}년 월별 손익 추이")
    _render_yearly_trend(br_sel, year, month)

    # ── 정산서 내보내기
    _render_pdf_section(full_df, br_sel, year, month)


# ── 지점 관리 탭 ──────────────────────────────────────────────
def _render_branch_mgmt():
    sec("지점 목록")
    st.caption("계약일·해지일·재계약 여부를 직접 수정하고 저장하세요. 비활성 지점은 드롭다운에서 자동으로 제외됩니다.")

    branches = get_all_branches(active_only=False)
    if not branches:
        st.info("등록된 지점이 없습니다.")
        return

    display_cols = {
        "id":               "ID",
        "name":             "지점명",
        "contract_date":    "계약일",
        "termination_date": "해지일",
        "is_active":        "재계약",
        "note":             "비고",
    }

    df = pd.DataFrame(branches)
    edit_df = df[[c for c in display_cols if c in df.columns]].copy()
    edit_df = edit_df.rename(columns=display_cols)
    edit_df["재계약"] = edit_df["재계약"].apply(lambda v: bool(v))

    edited = st.data_editor(
        edit_df,
        use_container_width=True,
        hide_index=True,
        height=500,
        num_rows="fixed",
        key="branch_editor_table",
        column_config={
            "ID":   st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "지점명": st.column_config.TextColumn("지점명", width="large"),
            "계약일": st.column_config.TextColumn("계약일", width="medium",
                                                   help="YYYY-MM-DD 형식"),
            "해지일": st.column_config.TextColumn("해지일", width="medium",
                                                   help="계약 해지일 (비워두면 운영중)"),
            "재계약": st.column_config.CheckboxColumn("재계약", width="small",
                                                       help="체크 해제 시 드롭다운에서 제외"),
            "비고":  st.column_config.TextColumn("비고"),
        },
    )
    st.caption(f"총 {len(branches)}개 지점 · 셀 클릭 후 수정, 저장 버튼 클릭")

    if st.button("💾 변경사항 저장", key="branch_inline_save", type="primary"):
        changes = st.session_state.get("branch_editor_table", {}).get("edited_rows", {})
        if not changes:
            st.info("변경된 내용이 없습니다.")
        else:
            col_reverse = {v: k for k, v in display_cols.items()}
            saved_count = 0
            for row_idx_str, row_changes in changes.items():
                branch = dict(branches[int(row_idx_str)])
                for col_label, val in row_changes.items():
                    db_col = col_reverse.get(col_label)
                    if not db_col:
                        continue
                    if db_col == "is_active":
                        branch[db_col] = 1 if val else 0
                    else:
                        branch[db_col] = str(val or "").strip()
                upsert_branch(branch)
                saved_count += 1
            st.success(f"✅ {saved_count}개 지점 수정 완료")
            st.rerun()

    st.divider()
    sec("지점 추가")
    c1, c2, c3 = st.columns(3)
    new_name     = c1.text_input("지점명 *", key="new_br_name")
    new_contract = c2.text_input("계약일 (YYYY-MM-DD)", key="new_br_contract")
    new_note     = c3.text_input("비고", key="new_br_note")
    if st.button("➕ 지점 추가", type="primary", key="new_br_save"):
        if not new_name.strip():
            st.error("지점명을 입력하세요.")
        else:
            upsert_branch({
                "name":          new_name.strip(),
                "contract_date": new_contract.strip(),
                "is_active":     1,
                "note":          new_note.strip(),
            })
            st.success(f"✅ '{new_name}' 지점 추가 완료")
            st.rerun()


# ── 월별 매출 입력 탭 ─────────────────────────────────────────
_REVENUE_COLS = {
    "dogeub":       "도급비",
    "pt_sales":     "PT매출",
    "gx_sales":     "GX매출",
    "cafe_sales":   "카페매출",
    "golf_sales":   "골프매출",
    "facility_fee": "시설상환비",
    "cafe_labor":   "카페인건비",
    "other_sales":  "기타매출",
}


def _render_monthly_revenue(year: int, month: int):
    sec("월별 매출 직접 입력")
    st.caption("카드/통장 데이터 외 별도로 관리할 매출 항목을 지점별로 입력하세요.")

    col1, col2 = st.columns(2)
    yrs   = list(range(_now.year, _now.year - 3, -1))
    year  = col1.selectbox("연도", yrs,
                            index=yrs.index(year) if year in yrs else 0,
                            key="bmr_yr")
    month = col2.selectbox("월", list(range(1, 13)), index=month - 1,
                            key="bmr_mn", format_func=lambda m: f"{m}월")

    BRANCH_LIST = get_active_branch_names()

    # 기존 저장값 불러오기
    saved = {r["branch"]: r for r in get_branch_monthly_revenue(year, month)}

    # 전체 지점 × 전체 컬럼 DataFrame 구성
    rows = []
    for br in BRANCH_LIST:
        s = saved.get(br, {})
        row = {"지점": br}
        for db_col, label in _REVENUE_COLS.items():
            row[label] = int(s.get(db_col, 0) or 0)
        row["비고"] = s.get("note", "")
        rows.append(row)

    df_input = pd.DataFrame(rows)

    edited = st.data_editor(
        df_input,
        use_container_width=True,
        hide_index=True,
        height=600,
        num_rows="fixed",
        key="bmr_editor",
        column_config={
            "지점": st.column_config.TextColumn("지점", disabled=True, width="large"),
            **{
                label: st.column_config.NumberColumn(label, format="%d", min_value=0, step=10000)
                for label in _REVENUE_COLS.values()
            },
            "비고": st.column_config.TextColumn("비고"),
        },
    )

    label_to_db = {v: k for k, v in _REVENUE_COLS.items()}

    if st.button("💾 저장", type="primary", key="bmr_save"):
        changes = st.session_state.get("bmr_editor", {}).get("edited_rows", {})
        if not changes:
            st.info("변경된 내용이 없습니다.")
        else:
            saved_count = 0
            for row_idx_str, row_changes in changes.items():
                br = BRANCH_LIST[int(row_idx_str)]
                # 기존값 + 변경값 병합
                existing = saved.get(br, {})
                data = {db_col: int(existing.get(db_col, 0) or 0)
                        for db_col in _REVENUE_COLS}
                data["note"] = existing.get("note", "")
                for col_label, val in row_changes.items():
                    if col_label == "비고":
                        data["note"] = str(val or "").strip()
                    elif col_label in label_to_db:
                        data[label_to_db[col_label]] = int(val or 0)
                upsert_branch_monthly_revenue(year, month, br, data)
                saved_count += 1
            st.success(f"✅ {year}년 {month}월 {saved_count}개 지점 매출 저장 완료")
            st.rerun()


def _render_pdf_section(full_df, br_sel: str, year: int, month: int):
    from domains.branch.pdf import gen_pdf_html
    _ALL_BRANCHES = get_active_branch_names()
    sec("정산서 내보내기")
    st.markdown(
        '<div class="al al-info">ℹ️&nbsp; 포함할 지점을 선택한 후 다운로드하세요. '
        '브라우저에서 열고 Ctrl+P → PDF 저장</div>',
        unsafe_allow_html=True,
    )

    chk_all_br = st.checkbox("전체 지점 선택", value=False, key="pdf_all_br")
    if chk_all_br:
        available_br = [b for b in _ALL_BRANCHES
                        if not full_df[full_df.branch == b].empty
                        and full_df[full_df.branch == b].iloc[0]["총매출"] > 0]
        pdf_branches = available_br or [br_sel]
    else:
        available_br = [b for b in _ALL_BRANCHES if not full_df[full_df.branch == b].empty]
        rows_c = [st.columns(4) for _ in range((len(available_br) + 3) // 4)]
        flat   = [c for row_c in rows_c for c in row_c]
        pdf_branches = [b for b, col in zip(available_br, flat)
                        if col.checkbox(b, value=(b == br_sel), key=f"pdf_br_{b}")]

    if pdf_branches:
        exp_df_pdf   = c_exp(year, month)
        rev_df_pdf   = c_rev(year, month)
        html_content = gen_pdf_html(full_df, pdf_branches, year, month,
                                    exp_df=exp_df_pdf, rev_df=rev_df_pdf)
        html_b64 = base64.b64encode(html_content.encode("utf-8")).decode()
        btn_part = (
            f'<a href="data:text/html;base64,{html_b64}" '
            f'download="정산보고서_{year}년{month}월.html" '
            f'style="background:#E60028;color:#fff;border-radius:8px;font-weight:600;'
            f'font-size:14px;padding:10px 22px;text-decoration:none;'
            f'white-space:nowrap;display:inline-block;'
            f'box-shadow:0 2px 6px rgba(230,0,40,.3)">📄 정산서 다운로드</a>'
        )
    else:
        btn_part = (
            '<span style="background:#ccc;color:#fff;border-radius:8px;font-weight:600;'
            'font-size:14px;padding:10px 22px;white-space:nowrap;display:inline-block;'
            'cursor:not-allowed">정산서 다운로드</span>'
        )

    st.markdown(
        f'<div class="pdf-box" style="display:flex;align-items:center;'
        f'justify-content:space-between;flex-wrap:wrap;gap:14px">'
        f'<div><div class="pdf-t" style="margin-bottom:4px">📄 정산서 다운로드</div>'
        f'<div style="font-size:12px;color:#9A918C">선택 지점 {len(pdf_branches)}개 · {year}년 {month}월</div>'
        f'</div>{btn_part}</div>',
        unsafe_allow_html=True,
    )
