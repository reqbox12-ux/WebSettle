"""
domains/branch/ui.py — 지점 상세 페이지
"""
import base64
from datetime import datetime
import plotly.graph_objects as go
import streamlit as st

from shared.config import BRANCH_LIST
from shared.utils import fn, fw, sec, PLOT_BASE
from domains.dashboard.service import build_summary, c_rev, c_exp

_now = datetime.now()


# ── 지점 상세 패널 ───────────────────────────────────────────
def render_detail(row, year: int, month: int):
    b       = row["branch"]
    pnl     = int(row["손익"])
    rate    = row["이익률"]
    pnl_cls = "c-pos" if pnl >= 0 else "c-red"
    rate_bg = "background:var(--poss);color:var(--pos)" if rate >= 0 else "background:var(--reds);color:var(--red)"
    sign    = "▲" if pnl >= 0 else "▼"

    CARD_CATS = ["PT매출(카드)", "GX매출(카드)", "골프매출(카드)", "키즈매출(카드)", "기타매출(카드)"]
    CASH_CATS = ["PT매출(현금)", "GX매출(현금)", "골프매출(현금)", "키즈매출(현금)", "기타매출(현금)",
                 "도급비", "시설상환비", "카페매출"]

    def dr(lbl, amt, cls="", sub=False, bold=False):
        row_cls = "dp-row sub" if sub else "dp-row"
        if bold:
            row_cls += " tot"
        lbl_cls = "dp-lbl m" if bold else "dp-lbl"
        amt_cls = f"dp-amt {cls}" if cls else "dp-amt"
        return (
            f'<div class="{row_cls}"><span class="{lbl_cls}">{lbl}</span>'
            f'<span class="{amt_cls}">{fn(amt)}원</span></div>'
        )

    rev_df  = c_rev(year, month)
    rev_by_cat = {}
    if not rev_df.empty:
        br_rev = rev_df[rev_df.branch == b]
        rev_by_cat = br_rev.set_index("category")["supply_amount"].to_dict()

    card_rows = "".join(dr(cat, int(rev_by_cat.get(cat, 0)), sub=True)
                        for cat in CARD_CATS if int(rev_by_cat.get(cat, 0)) > 0)
    if not card_rows:
        card_rows = '<div class="dp-row sub"><span class="dp-lbl">내역 없음</span><span class="dp-amt">—</span></div>'

    cash_rows = "".join(dr(cat, int(rev_by_cat.get(cat, 0)), sub=True)
                        for cat in CASH_CATS if int(rev_by_cat.get(cat, 0)) > 0)
    if not cash_rows:
        cash_rows = '<div class="dp-row sub"><span class="dp-lbl">내역 없음</span><span class="dp-amt">—</span></div>'

    card_fee_html = ""
    if int(row["카드수수료"]) > 0 or int(row["카드VAT"]) > 0:
        card_fee_html = (
            f'<div class="dp-row sub" style="color:var(--ink3);font-size:12px">'
            f'<span>부가세 {fn(row["카드VAT"])}원 · 수수료 {fn(row["카드수수료"])}원 차감</span></div>'
        )

    card_html = f"""
    <div class="dp-sec">
      <div class="dp-sec-t">카드 매출 세부</div>
      {card_rows}{card_fee_html}
      <div class="dp-row tot"><span class="dp-lbl m">카드 실수령</span>
        <span class="dp-amt c-ink">{fn(row["카드실수령"])}원</span></div>
    </div>"""

    cash_html = f"""
    <div class="dp-sec" style="margin-top:16px">
      <div class="dp-sec-t">현금·기타 매출 세부</div>
      {cash_rows}
      <div class="dp-row sub" style="color:var(--ink3);font-size:12px">
        <span>부가세 {fn(row["현금VAT"])}원 차감</span></div>
      <div class="dp-row tot"><span class="dp-lbl m">현금 공급가액</span>
        <span class="dp-amt c-ink">{fn(row["현금공급가액"])}원</span></div>
    </div>"""

    exp_df    = c_exp(year, month)
    exp_by_cat: dict = {}
    if not exp_df.empty:
        br_exp     = exp_df[exp_df.branch == b]
        exp_by_cat = br_exp.groupby("category")["amount"].sum().to_dict()

    pay_rows = ""
    for lbl, key in [
        ("급여 (실수령)",        "급여"),
        ("4대보험료 (직원부담)", "4대보험료_직원"),
        ("4대보험료 (본사부담)", "4대보험_본사"),
        ("소득세·지방세",        "소득세지방세"),
        ("프리랜서",             "프리랜서"),
        ("프리랜서 세금",        "프리랜서세금"),
    ]:
        if int(row.get(key, 0)) > 0:
            pay_rows += dr(lbl, row[key], sub=True)

    other_rows = "".join(
        dr(cat, amt, sub=True)
        for cat, amt in sorted(exp_by_cat.items(), key=lambda x: -x[1])
        if amt > 0
    )

    exp_html = f"""
    <div class="dp-sec">
      <div class="dp-sec-t">지출 상세</div>
      {dr("인건비 합계", row["인건비합계"], bold=True)}
      {pay_rows or '<div class="dp-row sub"><span class="dp-lbl">내역 없음</span><span class="dp-amt">—</span></div>'}
      {dr("기타지출 합계", row["기타지출"], bold=True)}
      {other_rows or '<div class="dp-row sub"><span class="dp-lbl">내역 없음</span><span class="dp-amt">—</span></div>'}
      {dr("부가세 합계", row["부가세합계"], bold=True)}
      <div class="dp-row tot"><span class="dp-lbl m">총 지출</span>
        <span class="dp-amt c-red">{fn(row["총지출"])}원</span></div>
    </div>"""

    html = f"""
    <div class="dp">
      <div class="dp-hd">
        <span class="dp-title">{b} 상세</span>
        <div class="dp-profit">
          <span class="dp-profit-val {pnl_cls}">{sign} {fn(abs(pnl))}원</span>
          <span class="dp-profit-rate" style="{rate_bg}">{"+" if rate >= 0 else ""}{rate}%</span>
        </div>
      </div>
      <div class="dp-cols">
        <div>{card_html}{cash_html}</div>
        <div>{exp_html}</div>
      </div>
    </div>"""
    st.markdown(html, unsafe_allow_html=True)


# ── 지점 페이지 메인 ─────────────────────────────────────────
def render_page():
    year  = st.session_state.year
    month = st.session_state.month

    st.markdown(
        '<div class="ph"><div class="ph-title">지점 상세 내역</div>'
        '<div class="ph-sub">지점을 선택하면 매출·지출 상세 내역을 확인합니다</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns([1, 1, 2])
    yrs    = list(range(_now.year, _now.year - 3, -1))
    year   = fc1.selectbox("연도", yrs, index=yrs.index(year) if year in yrs else 0, key="br_yr")
    month  = fc2.selectbox("월", list(range(1, 13)), index=month - 1, key="br_mn", format_func=lambda m: f"{m}월")
    br_sel = fc3.selectbox("지점 선택", BRANCH_LIST, key="br_sel")
    st.session_state.year  = year
    st.session_state.month = month
    st.markdown('</div>', unsafe_allow_html=True)

    with st.spinner("데이터 로드 중..."):
        full_df = build_summary(year, month)

    br_row   = full_df[full_df.branch == br_sel]
    has_data = (not br_row.empty and
                (br_row.iloc[0]["총매출"] != 0 or br_row.iloc[0]["총지출"] != 0))

    if not has_data:
        _rev_check = c_rev(year, month)
        _exp_check = c_exp(year, month)
        _has_bank  = ((not _rev_check.empty and br_sel in _rev_check.branch.values) or
                      (not _exp_check.empty and br_sel in _exp_check.branch.values))
        if not _has_bank:
            st.markdown('<div class="al al-warn">⚠️&nbsp; 해당 지점의 데이터가 없습니다.</div>',
                        unsafe_allow_html=True)
        else:
            has_data = True

    if has_data:
        if br_row.empty:
            import pandas as pd
            dummy = {c: 0 for c in full_df.columns}
            dummy["branch"] = br_sel
            br_row = pd.DataFrame([dummy])
        render_detail(br_row.iloc[0], year, month)

        # 월별 추이
        sec("월별 손익 추이")
        months_data = []
        for m in range(1, 13):
            r     = build_summary(year, m)
            row_m = r[r.branch == br_sel]
            if not row_m.empty:
                months_data.append({"월": f"{m}월",
                                    "총매출": row_m.iloc[0]["총매출"],
                                    "총지출": row_m.iloc[0]["총지출"],
                                    "손익":   row_m.iloc[0]["손익"]})
            else:
                months_data.append({"월": f"{m}월", "총매출": 0, "총지출": 0, "손익": 0})

        import pandas as pd
        mdf = pd.DataFrame(months_data)
        fig_br = go.Figure()
        fig_br.add_trace(go.Bar(name="총매출", x=mdf["월"], y=mdf["총매출"],
                                marker_color="#3D3835", opacity=0.8))
        fig_br.add_trace(go.Bar(name="총지출", x=mdf["월"], y=mdf["총지출"],
                                marker_color="#E60028", opacity=0.75))
        fig_br.add_trace(go.Scatter(
            name="손익", x=mdf["월"], y=mdf["손익"],
            mode="lines+markers", yaxis="y2",
            line=dict(color="#2E7D5B", width=2.5),
            marker=dict(size=8, color=["#2E7D5B" if v >= 0 else "#E60028" for v in mdf["손익"]],
                        line=dict(width=2, color="white")),
        ))
        fig_br.update_layout(**{
            **PLOT_BASE, "barmode": "group", "height": 320,
            "yaxis":  dict(tickformat=",", gridcolor="rgba(31,27,27,.08)", zeroline=False),
            "yaxis2": dict(overlaying="y", side="right", tickformat=",",
                           zeroline=True, zerolinecolor="rgba(31,27,27,.2)"),
            "xaxis":  dict(tickfont=dict(size=11)),
        })
        st.plotly_chart(fig_br, use_container_width=True)

        # 정산서 다운로드
        _render_pdf_section(full_df, br_sel, year, month)


def _render_pdf_section(full_df, br_sel: str, year: int, month: int):
    from domains.branch.pdf import gen_pdf_html
    sec("정산서 내보내기")
    st.markdown(
        '<div class="al al-info">ℹ️&nbsp; 포함할 지점을 선택한 후 다운로드하세요. '
        '브라우저에서 열고 Ctrl+P → PDF 저장</div>',
        unsafe_allow_html=True,
    )

    chk_all_br = st.checkbox("전체 지점 선택", value=False, key="pdf_all_br")
    if chk_all_br:
        available_br = [b for b in BRANCH_LIST
                        if not full_df[full_df.branch == b].empty
                        and full_df[full_df.branch == b].iloc[0]["총매출"] > 0]
        pdf_branches = available_br or [br_sel]
    else:
        available_br = [b for b in BRANCH_LIST if not full_df[full_df.branch == b].empty]
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
