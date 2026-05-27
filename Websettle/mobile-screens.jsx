// mobile-screens.jsx — Mobile artboards for WebSettle (in iOS frames)

const { useState: mUseState } = React;

// Bottom tab bar
function MobileTabBar({ active = 'home' }) {
  const items = [
    { id: 'home', label: '홈', icon: I.Home2 },
    { id: 'settle', label: '정산', icon: I.Wallet },
    { id: 'branch', label: '지점', icon: I.Building },
    { id: 'report', label: '리포트', icon: I.Chart },
    { id: 'me', label: '내정보', icon: I.User },
  ];
  return (
    <div style={{
      position: 'absolute', bottom: 0, left: 0, right: 0,
      background: 'rgba(255,255,255,0.92)',
      borderTop: '1px solid var(--border)',
      backdropFilter: 'blur(20px)',
      padding: '8px 8px 28px',
      display: 'flex', justifyContent: 'space-around',
      zIndex: 5,
    }}>
      {items.map(it => {
        const Icon = it.icon;
        const isActive = it.id === active;
        return (
          <div key={it.id} style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
            padding: '6px 8px',
            color: isActive ? 'var(--laon-red)' : 'var(--ink-3)',
          }}>
            <Icon size={22} sw={isActive ? 2 : 1.7}/>
            <span style={{ fontSize: 10, fontWeight: isActive ? 700 : 500 }}>{it.label}</span>
          </div>
        );
      })}
    </div>
  );
}

function MobileTopNav({ title, leading, trailing, transparent = false }) {
  return (
    <div style={{
      padding: '12px 20px 14px',
      display: 'flex', alignItems: 'center', gap: 12,
      background: transparent ? 'transparent' : 'var(--surface)',
      borderBottom: transparent ? 'none' : '1px solid var(--border)',
      position: 'relative', zIndex: 2,
    }}>
      <div style={{ width: 32, display: 'flex', alignItems: 'center' }}>{leading}</div>
      <h1 style={{ flex: 1, textAlign: 'center', fontSize: 16, fontWeight: 700, letterSpacing: '-0.01em', margin: 0 }}>{title}</h1>
      <div style={{ width: 32, display: 'flex', justifyContent: 'flex-end' }}>{trailing}</div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Mobile Login
// ──────────────────────────────────────────────────────────────────────
function MobileLogin() {
  return (
    <div className="ws-root" style={{ width: '100%', height: '100%', background: 'var(--bg)', display: 'flex', flexDirection: 'column' }}>
      <IOSStatusBar/>
      <div style={{ flex: 1, padding: '8px 28px 28px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ marginTop: 30, marginBottom: 'auto' }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14,
            background: 'var(--laon-red)', display: 'inline-flex',
            alignItems: 'center', justifyContent: 'center', color: '#fff',
            fontWeight: 800, fontSize: 22, letterSpacing: '-0.02em',
            marginBottom: 22,
          }}>WS</div>
          <h1 style={{ fontSize: 30, fontWeight: 800, letterSpacing: '-0.03em', margin: 0, lineHeight: 1.15 }}>
            안녕하세요,<br/>다시 만나요.
          </h1>
          <p style={{ fontSize: 14, color: 'var(--ink-2)', marginTop: 10 }}>LAON SPORTS 사내 계정으로 로그인하세요.</p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
          <MobileField label="사번 또는 이메일" icon={<I.Mail size={16}/>} value="kjy@laonsports.com"/>
          <MobileField label="비밀번호" icon={<I.Lock size={16}/>} type="password" value="************"/>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 2 }}>
            <a style={{ fontSize: 13, color: 'var(--laon-red)', fontWeight: 600, textDecoration: 'none' }}>비밀번호 찾기</a>
          </div>
          <WsBtn variant="red" size="lg" style={{ width: '100%', height: 52, fontSize: 15, marginTop: 12 }}>로그인</WsBtn>
          <WsBtn variant="ghost" size="lg" style={{ width: '100%', height: 52, fontSize: 14 }} icon={<I.User size={16}/>}>Face ID로 로그인</WsBtn>
        </div>

        <div style={{ fontSize: 11.5, color: 'var(--ink-3)', textAlign: 'center', paddingBottom: 20 }}>
          v2.4.1 · © 2026 LAON SPORTS
        </div>
      </div>
    </div>
  );
}

function MobileField({ label, icon, type = 'text', value }) {
  return (
    <div>
      <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--ink-2)', display: 'block', marginBottom: 6 }}>{label}</label>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '0 14px', height: 50,
        background: 'var(--surface)', border: '1px solid var(--border-strong)', borderRadius: 12,
      }}>
        {icon && <span style={{ color: 'var(--ink-3)' }}>{icon}</span>}
        <input type={type} defaultValue={value} style={{
          flex: 1, border: 0, outline: 0, background: 'transparent',
          color: 'var(--ink)', fontSize: 15,
        }}/>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Mobile Home (Dashboard)
// ──────────────────────────────────────────────────────────────────────
function MobileHome({ chartType = 'area' }) {
  const d = window.wsData;
  return (
    <div className="ws-root" style={{ width: '100%', height: '100%', background: 'var(--bg)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <IOSStatusBar/>
      <div style={{ flex: 1, overflow: 'auto', paddingBottom: 96 }}>
        {/* Header gradient block */}
        <div style={{
          padding: '10px 20px 20px',
          background: 'linear-gradient(180deg, var(--ink) 0%, #2A2625 100%)',
          color: '#F5F1ED',
          borderRadius: '0 0 22px 22px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Avatar name="김재영" size={36}/>
              <div>
                <div style={{ fontSize: 11, opacity: 0.6 }}>김재영 본부장</div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>경영지원본부</div>
              </div>
            </div>
            <button style={{ ...iconBtn, background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', color: '#F5F1ED' }}>
              <I.Bell size={18}/>
              <span style={{ ...dotBadge, boxShadow: '0 0 0 2px #2A2625' }}/>
            </button>
          </div>

          <div style={{ fontSize: 11.5, opacity: 0.55, fontWeight: 600, letterSpacing: '0.06em' }}>4월 정산 · 마감</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 8 }}>
            <span className="ws-tnum" style={{ fontSize: 38, fontWeight: 800, letterSpacing: '-0.025em' }}>19.56</span>
            <span style={{ fontSize: 18, opacity: 0.7 }}>억 원</span>
            <span style={{ marginLeft: 'auto', fontSize: 13, color: '#7CE7AC', fontWeight: 700 }}>+13.7%</span>
          </div>
          <div style={{ marginTop: 14, height: 56 }}>
            <MiniArea data={d.monthly.revenue} color="#fff" height={56}/>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 10, color: 'rgba(245,241,237,0.5)' }}>
            {d.monthly.labels.map(l => <span key={l}>{l}</span>)}
          </div>
        </div>

        {/* KPI cards */}
        <div style={{ padding: '18px 16px 12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {[
            { l: '순이익', v: '10.23', u: '억', dlt: 19.4, tone: 'pos' },
            { l: '환불액', v: '42.8', u: '백만', dlt: -4.2, tone: 'red' },
            { l: '활성 회원', v: '8,596', u: '명', dlt: 2.8 },
            { l: '평균 결제', v: '89.6', u: '만', dlt: 9.2 },
          ].map((k, i) => (
            <div key={i} style={{ padding: 14, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14 }}>
              <div style={{ fontSize: 11, color: 'var(--ink-3)', fontWeight: 500 }}>{k.l}</div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 3, marginTop: 6 }}>
                <span className="ws-tnum" style={{ fontSize: 20, fontWeight: 700, letterSpacing: '-0.02em' }}>{k.v}</span>
                <span style={{ fontSize: 11, color: 'var(--ink-3)' }}>{k.u}</span>
              </div>
              <div style={{ marginTop: 4 }}><WsDelta value={k.dlt}/></div>
            </div>
          ))}
        </div>

        {/* Branch list */}
        <div style={{ padding: '14px 16px 8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, letterSpacing: '-0.015em' }}>지점별 매출</h3>
          <a style={{ fontSize: 12, color: 'var(--ink-3)' }}>전체 →</a>
        </div>
        <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          {d.branches.slice(0, 4).map(b => {
            const colors = { gn: '#E60028', bd: '#1F1B1B', js: '#3963A8', sd: '#2E7D5B', gk: '#B86E1F', hd: '#7340B7' };
            return (
              <div key={b.id} style={{
                padding: 14, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12,
                display: 'flex', alignItems: 'center', gap: 12,
              }}>
                <span style={{ width: 38, height: 38, borderRadius: 10, background: colors[b.id] || 'var(--ink)', color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 12 }}>{b.name.slice(0,2)}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13.5, fontWeight: 700, letterSpacing: '-0.01em' }}>{b.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--ink-3)' }} className="ws-mono">{b.code} · {b.region}</div>
                </div>
                <div style={{ width: 56, height: 28 }}><MiniArea data={b.trend} color={b.delta >= 0 ? 'var(--ink)' : 'var(--laon-red)'} height={28}/></div>
                <div style={{ textAlign: 'right' }}>
                  <div className="ws-tnum" style={{ fontSize: 13, fontWeight: 700 }}>{wsKRW(b.revenue)}</div>
                  <div style={{ marginTop: 2 }}><WsDelta value={b.delta}/></div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Alerts */}
        <div style={{ padding: '20px 16px 8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, letterSpacing: '-0.015em' }}>주의 필요</h3>
          <span style={{ fontSize: 11, color: 'var(--laon-red)', fontWeight: 700 }}>3건</span>
        </div>
        <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          {d.alerts.map(a => (
            <div key={a.id} style={{
              padding: 14, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12,
              display: 'flex', gap: 12, alignItems: 'flex-start',
            }}>
              <span style={{ width: 8, height: 8, borderRadius: 999, background: a.severity === 'high' ? 'var(--laon-red)' : a.severity === 'medium' ? 'var(--warn)' : 'var(--info)', marginTop: 6 }}/>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13.5, fontWeight: 600 }}>{a.title}</div>
                <div style={{ fontSize: 12, color: 'var(--ink-2)', marginTop: 2 }}>{a.desc}</div>
                <div style={{ fontSize: 10.5, color: 'var(--ink-3)', marginTop: 4 }}>{a.when}</div>
              </div>
              <I.ChevronRight size={14} style={{ color: 'var(--ink-3)', marginTop: 4 }}/>
            </div>
          ))}
        </div>
      </div>
      <MobileTabBar active="home"/>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Mobile Settlement Detail (full-screen drilldown)
// ──────────────────────────────────────────────────────────────────────
function MobileSettlement({ chartType = 'area' }) {
  const d = window.wsData;
  return (
    <div className="ws-root" style={{ width: '100%', height: '100%', background: 'var(--bg)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <IOSStatusBar/>
      <MobileTopNav
        title="정산 상세"
        leading={<button style={{ border: 0, background: 'transparent', padding: 4 }}><I.ChevronLeft size={22}/></button>}
        trailing={<button style={{ border: 0, background: 'transparent', padding: 4 }}><I.More size={20}/></button>}
      />
      <div style={{ flex: 1, overflow: 'auto', paddingBottom: 92 }}>
        {/* hero */}
        <div style={{ padding: '20px 20px 16px' }}>
          <div style={{ fontSize: 12, color: 'var(--ink-3)', fontWeight: 500 }}>강남 본점 · 4월 정산</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 6 }}>
            <span className="ws-tnum" style={{ fontSize: 34, fontWeight: 800, letterSpacing: '-0.025em' }}>384.2</span>
            <span style={{ fontSize: 17, color: 'var(--ink-2)' }}>백만 원</span>
            <span style={{ marginLeft: 'auto' }}><WsDelta value={8.2} big/></span>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
            <SegPills items={['1주', '1개월', '3개월', '6개월', '1년']} active="1개월"/>
          </div>
          <div style={{ marginTop: 12, padding: 14, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14 }}>
            <ChartArea
              chartType={chartType}
              height={170}
              labels={['1', '5', '10', '15', '20', '25', '30']}
              series={[{ name: '매출', values: [9.8, 12.4, 11.2, 14.6, 13.8, 16.4, 18.2].map(v => v * 1e6), color: 'var(--laon-red)' }]}
            />
          </div>
        </div>

        {/* segments */}
        <div style={{ padding: '0 16px' }}>
          <h3 style={{ margin: '8px 4px 10px', fontSize: 13, fontWeight: 700, color: 'var(--ink-3)', letterSpacing: '0.06em' }}>매출 구성</h3>
          <div style={{ padding: 14, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, display: 'flex', gap: 14, alignItems: 'center' }}>
            <Donut
              segments={[
                { label: '월회비', value: 248, color: 'var(--ink)' },
                { label: 'PT/레슨', value: 92, color: 'var(--laon-red)' },
                { label: '부대', value: 44, color: 'var(--ink-4)' },
              ]}
              size={92} thickness={14}
              center={<span className="ws-tnum" style={{ fontSize: 15, fontWeight: 700 }}>384M</span>}
            />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                ['월회비', 248000000, 'var(--ink)'],
                ['PT/레슨',  92000000, 'var(--laon-red)'],
                ['부대수익',  44000000, 'var(--ink-4)'],
              ].map(([l, v, c], i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                  <span style={{ width: 7, height: 7, borderRadius: 999, background: c }}/>
                  <span style={{ flex: 1, color: 'var(--ink-2)' }}>{l}</span>
                  <span className="ws-tnum" style={{ fontWeight: 600 }}>{wsKRW(v)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* transactions */}
        <div style={{ padding: '20px 16px 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <h3 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: 'var(--ink-3)', letterSpacing: '0.06em' }}>최근 거래</h3>
            <a style={{ fontSize: 12, color: 'var(--ink-3)' }}>전체 →</a>
          </div>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, overflow: 'hidden' }}>
            {d.payments.slice(0, 5).map((p, i) => (
              <div key={p.id} style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '12px 14px',
                borderTop: i === 0 ? 'none' : '1px solid var(--border)',
              }}>
                <Avatar name={p.member} size={32}/>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{p.member} <span style={{ color: 'var(--ink-3)', fontWeight: 500, fontSize: 11 }}>· {p.type}</span></div>
                  <div style={{ fontSize: 10.5, color: 'var(--ink-3)' }} className="ws-mono">{p.id} · {p.ts.slice(11)}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="ws-tnum" style={{ fontSize: 13, fontWeight: 700, color: p.status === 'refunded' ? 'var(--laon-red)' : 'var(--ink)' }}>
                    {p.status === 'refunded' && '−'}{(p.amount / 1000).toFixed(0)}K
                  </div>
                  <div style={{ marginTop: 2 }}><PaymentStatusMini s={p.status}/></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* PDF CTA */}
        <div style={{ padding: '20px 16px 24px' }}>
          <WsBtn variant="red" size="lg" style={{ width: '100%', height: 52 }} icon={<I.Download size={16}/>}>정산서 PDF 출력</WsBtn>
        </div>
      </div>
      <MobileTabBar active="settle"/>
    </div>
  );
}

function PaymentStatusMini({ s }) {
  const map = {
    success: { c: 'var(--pos)',     l: '성공' },
    pending: { c: 'var(--warn)',    l: '진행' },
    refunded:{ c: 'var(--laon-red)', l: '환불' },
  };
  const v = map[s] || map.pending;
  return (
    <span style={{ fontSize: 10, color: v.c, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 3 }}>
      <span style={{ width: 5, height: 5, borderRadius: 999, background: v.c }}/>
      {v.l}
    </span>
  );
}

Object.assign(window, { MobileLogin, MobileHome, MobileSettlement });
