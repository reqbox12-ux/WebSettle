"""
domains/dashboard/ui.py — 전체 집계 대시보드 페이지
"""
from datetime import datetime
import plotly.graph_objects as go
import streamlit as st

from shared.config import BRANCH_LIST
from shared.utils import fw, fn, sec, PLOT_BASE
from domains.dashboard.service import build_summary, c_rev, c_exp


_now = datetime.now()

# ── KPI 카드 ────────────────────────────────────────────────
def render_kpi(df):
    tot_rev  = df["총매출"].sum()
    # 카드 매출 = 공급가액 + VAT + 수수료 (총액)
    card_rev = (df["카드공급가액"].fillna(0)
                + df["카드VAT"].fillna(0)
                + df["카드수수료"].fillna(0)).sum()
    # 현금 매출 = 공급가액 + VAT (총입금액)
    cash_rev = (df["현금공급가액"].fillna(0) + df["현금VAT"].fillna(0)).sum()
    tot_exp  = df["총지출"].sum()
    tot_pnl  = df["손익"].sum()
    # 이익률 = 손익 ÷ 총매출 × 100
    rate     = round(tot_pnl / tot_rev * 100, 1) if tot_rev else 0
    pc       = (df["손익"] > 0).sum()
    tc       = len(df[df["총매출"] > 0])
    sign_pnl = "▲" if tot_pnl >= 0 else "▼"
    sign_rt  = "+" if rate >= 0 else ""

    cards = [
        ("카드 매출",  fw(card_rev), "원", "공급가액+VAT+수수료",           "c-ink"),
        ("현금 매출",  fw(cash_rev), "원", "공급가액+VAT (총입금)",          "c-ink"),
        ("총 지출",    fw(tot_exp),  "원", "인건비 + 기타 + 부가세 + 수수료", "c-red"),
        ("순 손익",    f"{sign_pnl} {fw(abs(tot_pnl))}", "원", "총매출 – 총지출",
         "c-pos" if tot_pnl >= 0 else "c-red"),
        ("이익률",     f"{sign_rt}{rate}", "%", f"손익÷총매출 · 흑자 {pc} / {tc} 지점",
         "c-pos" if rate >= 0 else "c-red"),
    ]
    html = '<div class="kpi-grid">'
    for lbl, val, unit, sub, cls in cards:
        html += (
            f'<div class="kpi"><div class="kpi-lbl">{lbl}</div>'
            f'<div class="kpi-val {cls}">{val}<span class="kpi-unit">{unit}</span></div>'
            f'<div class="kpi-sub">{sub}</div></div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── 막대 + 손익 차트 ─────────────────────────────────────────
def render_chart(df, key="ch"):
    dc = df[df["총매출"] > 0].sort_values("총매출", ascending=False)
    if dc.empty:
        st.info("차트 데이터가 없습니다.")
        return
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="총매출", x=dc.branch, y=dc.총매출,
        marker_color="#3D3835", opacity=0.85,
        text=dc.총매출.apply(fw), textposition="outside",
        textfont=dict(size=10, color="#1F1B1B", family="Pretendard Variable,sans-serif"),
    ))
    fig.add_trace(go.Bar(
        name="총지출", x=dc.branch, y=dc.총지출,
        marker_color="#E60028", opacity=0.75,
    ))
    fig.add_trace(go.Scatter(
        name="손익", x=dc.branch, y=dc.손익,
        mode="lines+markers", yaxis="y2",
        line=dict(color="#2E7D5B", width=2.5),
        marker=dict(
            size=7,
            color=["#2E7D5B" if v >= 0 else "#E60028" for v in dc.손익],
            line=dict(width=2, color="white"),
        ),
    ))
    _tf = dict(size=11, color="#1F1B1B", family="Pretendard Variable,sans-serif")
    fig.update_layout(**{
        **PLOT_BASE, "barmode": "group", "height": 380,
        "yaxis":  dict(tickformat=",", gridcolor="rgba(31,27,27,.08)", zeroline=False, tickfont=_tf, color="#1F1B1B"),
        "yaxis2": dict(overlaying="y", side="right", tickformat=",", zeroline=True,
                       zerolinecolor="rgba(31,27,27,.2)", tickfont=_tf, color="#1F1B1B"),
        "xaxis":  dict(tickangle=-30, tickfont=_tf, color="#1F1B1B"),
        "margin": dict(t=16, b=70, l=10, r=10),
    })
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── 손익 순위 카드 ────────────────────────────────────────────
def render_rank_cards(df):
    active  = df[df["총매출"] > 0].sort_values("손익", ascending=False)
    if active.empty:
        st.info("데이터 없음")
        return
    top3    = active.head(3)
    bottom3 = active.tail(3).sort_values("손익")

    def card_row(row, rank, is_top):
        pnl  = int(row["손익"])
        rate = row["이익률"]
        sign = "▲" if pnl >= 0 else "▼"
        pnl_col  = "var(--pos)" if is_top else "var(--red)"
        bg       = "var(--poss)" if is_top else "var(--reds)"
        rate_col = "var(--pos)" if is_top else "var(--red)"
        rate_sign = ""
        return (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:10px 14px;border-radius:var(--rs);background:{bg};margin-bottom:6px">'
            f'<div style="display:flex;align-items:center;gap:10px">'
            f'<span style="font-size:12px;font-weight:800;color:{pnl_col};width:18px;text-align:center">{rank}</span>'
            f'<span style="font-size:13px;font-weight:600;color:var(--ink)">{row["branch"]}</span>'
            f'</div><div style="text-align:right">'
            f'<div style="font-size:13px;font-weight:700;color:{pnl_col}">{sign} {fw(abs(pnl))}</div>'
            f'<div style="font-size:11px;font-weight:600;color:{rate_col}">{rate_sign}{rate:.1f}%</div>'
            f'</div></div>'
        )

    html = '<div style="display:flex;flex-direction:column;gap:16px">'
    html += '<div><div style="font-size:10px;font-weight:700;color:var(--pos);letter-spacing:.07em;text-transform:uppercase;margin-bottom:8px">🏆 흑자 TOP 3</div>'
    for i, (_, row) in enumerate(top3.iterrows()):
        html += card_row(row, i + 1, True)
    html += '</div>'
    html += '<div><div style="font-size:10px;font-weight:700;color:var(--red);letter-spacing:.07em;text-transform:uppercase;margin-bottom:8px">⚠️ 적자 BOTTOM 3</div>'
    for i, (_, row) in enumerate(bottom3.iterrows()):
        html += card_row(row, i + 1, False)
    html += '</div></div>'
    st.markdown(html, unsafe_allow_html=True)


# ── 대시보드 페이지 메인 ─────────────────────────────────────
def render_page():
    year  = st.session_state.year
    month = st.session_state.month
    sel   = st.session_state.sel_br

    st.markdown(
        '<div class="ph"><div class="ph-title">대시보드</div>'
        '<div class="ph-sub">연도 · 월 · 지점을 선택하면 데이터가 필터링됩니다</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 2])
    yrs   = list(range(_now.year, _now.year - 3, -1))
    year  = c1.selectbox("연도", yrs, index=yrs.index(year) if year in yrs else 0, key="f_yr")
    month = c2.selectbox("월", list(range(1, 13)), index=month - 1, key="f_mn", format_func=lambda m: f"{m}월")
    sel   = c3.selectbox("지점", ["전체"] + BRANCH_LIST, key="f_br")
    st.session_state.year   = year
    st.session_state.month  = month
    st.session_state.sel_br = sel
    st.markdown('</div>', unsafe_allow_html=True)

    with st.spinner("데이터 로드 중..."):
        full_df = build_summary(year, month)

    view_df = full_df[full_df.branch == sel] if sel != "전체" else full_df

    render_kpi(view_df)

    sec(f"{year}년 {month}월 · {'전체 지점' if sel == '전체' else sel}")
    view_mode = st.radio("보기 방식", ["요약", "상세"], horizontal=True, key="tbl_mode")

    if view_mode == "상세":
        detail_cols = {
            "branch": "지점", "카드공급가액": "카드공급가액", "카드수수료": "카드수수료",
            "카드VAT": "카드VAT", "카드실수령": "카드실수령", "현금공급가액": "현금공급가액",
            "현금VAT": "현금VAT", "총매출": "총매출", "급여": "급여",
            "4대보험료_직원": "4대보험(직원)", "4대보험_본사": "4대보험(본사)",
            "소득세지방세": "소득세·지방세", "프리랜서": "프리랜서", "프리랜서세금": "프리랜서세금",
            "인건비합계": "인건비합계", "기타지출": "기타지출", "부가세합계": "부가세합계",
            "총지출": "총지출", "손익": "손익", "이익률": "이익률(%)",
        }
        import pandas as pd
        disp = view_df[[c for c in detail_cols if c in view_df.columns]].copy()
        disp = disp.rename(columns=detail_cols)

        def _color_pnl(val):
            try:
                v = float(str(val).replace(",", ""))
                if v > 0:
                    return "color:#2E7D5B;font-weight:700"
                if v < 0:
                    return "color:#E60028;font-weight:700"
            except Exception:
                pass
            return ""

        int_cols_det = [c for c in disp.columns if c not in ("지점", "이익률(%)")]
        for c in int_cols_det:
            disp[c] = disp[c].apply(lambda v: f"{int(v):,}" if pd.notna(v) else "0")
        disp["이익률(%)"] = disp["이익률(%)"].apply(lambda v: f"{float(v):.1f}%" if pd.notna(v) else "0%")

        st.dataframe(
            disp.style
            .map(_color_pnl, subset=["손익"])
            .set_properties(**{"text-align": "right"}, subset=int_cols_det)
            .set_properties(**{"font-weight": "700", "text-align": "left"}, subset=["지점"]),
            use_container_width=True, hide_index=True, height=600,
        )
    else:
        table_html = (
            '<div class="bt"><table>'
            '<thead><tr>'
            '<th style="text-align:left">지점</th>'
            '<th>카드매출</th><th>현금매출</th><th>총지출</th><th>손익 / 이익률</th>'
            '</tr></thead><tbody>'
        )
        for _, row in view_df.iterrows():
            pnl  = int(row["손익"])
            rt   = row["이익률"]
            sign = "▲" if pnl >= 0 else "▼"
            bdg_cls  = "bdg-pos" if pnl >= 0 else "bdg-neg"
            rate_col = "color:var(--pos)" if rt >= 0 else "color:var(--red)"
            rate_sign = "+" if rt >= 0 else ""
            sel_cls  = "sel" if st.session_state.drill == row.branch else ""
            card_tot = int(row.get("카드공급가액", 0) + row.get("카드VAT", 0) + row.get("카드수수료", 0))
            cash_tot = int(row.get("현금공급가액", 0) + row.get("현금VAT", 0))
            table_html += (
                f'<tr class="{sel_cls}">'
                f'<td>{row.branch}</td>'
                f'<td>{fw(card_tot)}</td>'
                f'<td>{fw(cash_tot)}</td>'
                f'<td>{fw(row["총지출"])}</td>'
                f'<td style="text-align:center">'
                f'<span class="bdg {bdg_cls}">{sign} {fw(abs(pnl))}</span>'
                f'&nbsp;<span style="font-size:11.5px;{rate_col}">'
                f'{rate_sign}{rt}%</span></td>'
                f'</tr>'
            )
        table_html += '</tbody></table></div>'
        st.markdown(table_html, unsafe_allow_html=True)

    sec("지점별 매출 · 지출 · 손익")
    col_ch1, col_ch2 = st.columns([3, 2])
    with col_ch1:
        st.markdown('<div class="ch"><div class="ch-t">매출 · 지출 비교</div><div class="ch-s">막대: 매출/지출 &nbsp;|&nbsp; 선: 손익 (우축)</div>', unsafe_allow_html=True)
        render_chart(view_df, key="ch_main")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_ch2:
        st.markdown('<div class="ch"><div class="ch-t">손익 순위</div><div class="ch-s">흑자 TOP3 · 적자 BOTTOM3</div>', unsafe_allow_html=True)
        render_rank_cards(view_df)
        st.markdown('</div>', unsafe_allow_html=True)
