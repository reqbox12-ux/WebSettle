// desktop-screens.jsx — Desktop artboards for WebSettle

const { useState: dUseState, useMemo: dUseMemo } = React;

// ──────────────────────────────────────────────────────────────────────
//  Shell helper — sidebar + content
// ──────────────────────────────────────────────────────────────────────
function DesktopShell({ width = 1440, height = 900, active, sidebarCollapsed, children, topbar }) {
  return (
    <div className="ws-root" style={{
      width, height, display: 'flex',
      background: 'var(--bg)', color: 'var(--ink)',
      overflow: 'hidden',
    }}>
      <WsSidebar collapsed={sidebarCollapsed} active={active}/>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, position: 'relative' }}>
        {topbar}
        <main style={{ flex: 1, overflow: 'auto', padding: '24px 28px 28px' }}>
          {children}
        </main>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  1. LOGIN
// ──────────────────────────────────────────────────────────────────────
function ScreenLogin({ width = 1280, height = 800 }) {
  const [pwShow, setPwShow] = dUseState(false);
  return (
    <div className="ws-root" style={{ width, height, display: 'flex', background: 'var(--bg)', overflow: 'hidden' }}>
      {/* Left brand */}
      <div style={{
        flex: 1.1, position: 'relative',
        background: 'linear-gradient(155deg, #1F1B1B 0%, #2A2625 70%, #1A1716 100%)',
        color: '#F5F1ED',
        padding: '56px 60px',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }}>
        {/* subtle texture */}
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0, opacity: 0.06 }}>
          <defs>
            <pattern id="grid-l" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#fff" strokeWidth="0.6"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid-l)"/>
        </svg>
        {/* red accent ribbon */}
        <div style={{
          position: 'absolute', right: -120, top: 80, width: 320, height: 320,
          background: 'var(--laon-red)', opacity: 0.14, filter: 'blur(60px)',
          borderRadius: 999,
        }}/>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, zIndex: 1 }}>
          <img src="assets/laon-logo.png" alt="LAON SPORTS" style={{ height: 28, filter: 'brightness(0) invert(0.45) sepia(1) saturate(8) hue-rotate(-20deg)' }}/>
        </div>

        <div style={{ marginTop: 'auto', zIndex: 1 }}>
          <div style={{ fontSize: 11.5, color: 'rgba(245,241,237,0.55)', fontWeight: 600, letterSpacing: '0.08em', marginBottom: 18 }}>WEBSETTLE · INTERNAL DASHBOARD</div>
          <h1 style={{ fontSize: 44, fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1.08, margin: 0, color: '#fff' }}>
            지표는 단순하게,<br/>판단은 빠르게.
          </h1>
          <p style={{ fontSize: 15, lineHeight: 1.6, color: 'rgba(245,241,237,0.7)', marginTop: 22, maxWidth: 440 }}>
            8개 지점의 매출·정산·손익을 한 화면에서. 라온스포츠 경영진을 위한 사내 대시보드.
          </p>

          {/* Stats strip */}
          <div style={{ display: 'flex', gap: 32, marginTop: 40, paddingTop: 24, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
            {[
              ['08', '운영 지점'],
              ['8,596', '활성 회원'],
              ['19.6억', '월 정산액'],
            ].map(([v, l]) => (
              <div key={l}>
                <div style={{ fontSize: 26, fontWeight: 700, color: '#fff', letterSpacing: '-0.02em' }} className="ws-tnum">{v}</div>
                <div style={{ fontSize: 11.5, color: 'rgba(245,241,237,0.55)', marginTop: 2 }}>{l}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 36, fontSize: 11, color: 'rgba(245,241,237,0.4)', zIndex: 1 }}>
          © 2026 LAON SPORTS Co., Ltd. · v2.4.1
        </div>
      </div>

      {/* Right form */}
      <div style={{ flex: 1, background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60 }}>
        <div style={{ width: 380 }}>
          <div style={{ fontSize: 12, color: 'var(--ink-3)', fontWeight: 600, letterSpacing: '0.06em', marginBottom: 6 }}>SIGN IN</div>
          <h2 style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.025em', margin: '0 0 8px' }}>안녕하세요, 다시 만나요.</h2>
          <p style={{ fontSize: 13.5, color: 'var(--ink-2)', margin: '0 0 32px' }}>사내 계정으로 로그인하세요.</p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Field label="사번 또는 이메일" icon={<I.Mail size={16}/>} placeholder="name@laonsports.com" value="kjy@laonsports.com"/>
            <Field label="비밀번호" icon={<I.Lock size={16}/>} placeholder="••••••••" type={pwShow ? 'text' : 'password'} value="************"
              right={
                <button onClick={() => setPwShow(!pwShow)} style={{ border: 0, background: 'transparent', color: 'var(--ink-3)', display: 'flex', cursor: 'pointer' }}>
                  {pwShow ? <I.EyeOff size={16}/> : <I.Eye size={16}/>}
                </button>
              }/>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 2 }}>
              <label style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 13, color: 'var(--ink-2)', cursor: 'pointer' }}>
                <span style={{
                  width: 16, height: 16, borderRadius: 4, background: 'var(--ink)',
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
                }}><I.Check size={12} sw={3}/></span>
                로그인 상태 유지
              </label>
              <a href="#" style={{ fontSize: 13, color: 'var(--laon-red)', textDecoration: 'none', fontWeight: 600 }}>비밀번호 찾기</a>
            </div>

            <WsBtn variant="red" size="lg" style={{ marginTop: 12 }}>로그인</WsBtn>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '8px 0', color: 'var(--ink-3)', fontSize: 11.5 }}>
              <span style={{ height: 1, background: 'var(--border)', flex: 1 }}/>
              <span>또는</span>
              <span style={{ height: 1, background: 'var(--border)', flex: 1 }}/>
            </div>

            <WsBtn variant="ghost" size="lg" icon={<svg width="16" height="16" viewBox="0 0 16 16"><rect width="16" height="16" rx="3" fill="#FEE500"/><path d="M8 4C5.5 4 3.5 5.5 3.5 7.4c0 1.2 .8 2.3 2 2.9l-.4 1.5c-.05.2 .15.3 .3 .2L7 11c.3 0 .7 .1 1 .1 2.5 0 4.5-1.5 4.5-3.4S10.5 4 8 4Z" fill="#3C1E1E"/></svg>}>
              카카오워크로 SSO 로그인
            </WsBtn>
          </div>

          <p style={{ fontSize: 12, color: 'var(--ink-3)', textAlign: 'center', marginTop: 32 }}>
            계정 발급은 IT 지원실 (#it-support) 로 문의
          </p>
        </div>
      </div>
    </div>
  );
}

function Field({ label, icon, right, type = 'text', placeholder, value }) {
  return (
    <div>
      <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--ink-2)', letterSpacing: '-0.005em', display: 'block', marginBottom: 6 }}>{label}</label>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '0 12px', height: 44,
        background: 'var(--surface)', border: '1px solid var(--border-strong)', borderRadius: 10,
      }}>
        {icon && <span style={{ color: 'var(--ink-3)' }}>{icon}</span>}
        <input type={type} placeholder={placeholder} defaultValue={value} style={{
          flex: 1, border: 0, outline: 0, background: 'transparent',
          color: 'var(--ink)', fontSize: 14, letterSpacing: '-0.005em',
        }}/>
        {right}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Common: PeriodPicker chip
// ──────────────────────────────────────────────────────────────────────
function PeriodChip({ value = '2026년 4월', icon = true }) {
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 8,
      padding: '6px 12px 6px 12px', height: 36, borderRadius: 10,
      background: 'var(--surface)', border: '1px solid var(--border-strong)',
      color: 'var(--ink)', fontSize: 13, fontWeight: 600,
    }}>
      {icon && <I.Calendar size={15}/>}
      {value}
      <I.ChevronDown size={14}/>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Variant A — 정산/매출 중심 대시보드
// ──────────────────────────────────────────────────────────────────────
function DashboardA({ width = 1440, height = 900, sidebarCollapsed = false, chartType = 'area' }) {
  const d = window.wsData;

  return (
    <DesktopShell width={width} height={height} active="dashboard" sidebarCollapsed={sidebarCollapsed}
      topbar={
        <WsTopbar
          title="대시보드"
          breadcrumbs={['WebSettle', '대시보드']}
          right={
            <>
              <PeriodChip/>
              <WsBtn variant="ghost" size="md" icon={<I.Download size={15}/>}>내보내기</WsBtn>
              <WsBtn variant="primary" size="md" icon={<I.Plus size={15}/>}>새 정산</WsBtn>
            </>
          }
        />
      }
    >
      {/* greeting + period summary */}
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 18 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, letterSpacing: '-0.015em' }}>
            안녕하세요 김재영 본부장님 <span style={{ color: 'var(--ink-3)', fontWeight: 500 }}>· 오늘은 2026년 5월 16일 토요일</span>
          </h2>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--ink-2)' }}>
            4월 정산은 <b style={{ color: 'var(--ink)' }}>19.56억 원</b>으로 마감되었습니다.
            전월 대비 <b style={{ color: 'var(--pos)' }}>+13.7%</b> 성장. 1건 연체 발생 — 검토 필요.
          </p>
        </div>
      </div>

      {/* KPI grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--gap-grid)' }}>
        <KPI label="총 매출"     value="19.56" currency="억" delta={13.7} sparkline={[14.5,16.2,16.8,15.4,17.2,19.56]} chartType={chartType}/>
        <KPI label="순이익"     value="10.23" currency="억" delta={19.4} sparkline={[7.3,8.3,8.7,7.5,8.6,10.23]} tone="pos" chartType={chartType}/>
        <KPI label="환불액"     value="42.8"  currency="백만" delta={-4.2} sparkline={[58,52,48,44,46,42.8]} chartType={chartType}/>
        <KPI label="활성 회원"  value="8,596" currency="명" delta={2.8} sparkline={[8120,8240,8310,8398,8462,8596]} chartType={chartType}/>
      </div>

      {/* Main chart + side */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.55fr 1fr', gap: 'var(--gap-grid)', marginTop: 'var(--gap-grid)' }}>
        <WsCard>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 12.5, color: 'var(--ink-3)', fontWeight: 500 }}>매출 vs 비용 추이</div>
              <h3 style={{ margin: '4px 0 0', fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em' }}>최근 6개월</h3>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <ChartLegend items={[
                { label: '매출', color: 'var(--ink)' },
                { label: '비용', color: 'var(--laon-red)' },
              ]}/>
              <SegPills items={['일', '주', '월', '분기']} active="월"/>
            </div>
          </div>
          <ChartArea
            chartType={chartType}
            height={244}
            labels={d.monthly.labels}
            series={[
              { name: '매출', values: d.monthly.revenue, color: '#1F1B1B' },
              { name: '비용', values: d.monthly.cost,    color: '#E60028' },
            ]}
          />
        </WsCard>

        <WsCard>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 12.5, color: 'var(--ink-3)', fontWeight: 500 }}>4월 비용 구성</div>
              <h3 style={{ margin: '4px 0 0', fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em' }}>93.3M 원</h3>
            </div>
            <button style={iconBtn}><I.More size={16}/></button>
          </div>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <Donut
              segments={d.expenses.map(e => ({ ...e, value: e.value }))}
              size={134} thickness={20}
              center={<>
                <span className="ws-tnum" style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em' }}>933M</span>
                <span style={{ fontSize: 10.5, color: 'var(--ink-3)' }}>전월 +8.0%</span>
              </>}
            />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {d.expenses.slice(0, 5).map((e, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: e.color }}/>
                  <span style={{ flex: 1, color: 'var(--ink-2)' }}>{e.label}</span>
                  <span className="ws-tnum" style={{ fontWeight: 600 }}>{wsKRW(e.value)}</span>
                </div>
              ))}
            </div>
          </div>
        </WsCard>
      </div>

      {/* Branch table + alerts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.55fr 1fr', gap: 'var(--gap-grid)', marginTop: 'var(--gap-grid)' }}>
        <BranchTable data={d.branches.slice(0, 6)}/>
        <AlertsCard data={d.alerts}/>
      </div>
    </DesktopShell>
  );
}

function ChartLegend({ items }) {
  return (
    <div style={{ display: 'flex', gap: 14, fontSize: 11.5, color: 'var(--ink-2)' }}>
      {items.map(it => (
        <span key={it.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
          <span style={{ width: 8, height: 8, borderRadius: 999, background: it.color }}/>
          {it.label}
        </span>
      ))}
    </div>
  );
}

function SegPills({ items, active }) {
  return (
    <div style={{ display: 'inline-flex', background: 'var(--surface-2)', borderRadius: 8, padding: 3 }}>
      {items.map(it => (
        <button key={it} style={{
          padding: '4px 12px', fontSize: 11.5, fontWeight: 600, borderRadius: 6,
          background: it === active ? 'var(--surface)' : 'transparent',
          color: it === active ? 'var(--ink)' : 'var(--ink-3)',
          border: 0, boxShadow: it === active ? 'var(--shadow-sm)' : 'none',
        }}>{it}</button>
      ))}
    </div>
  );
}

function BranchTable({ data }) {
  return (
    <WsCard padded={false}>
      <div style={{ padding: '18px 22px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, letterSpacing: '-0.015em' }}>지점별 매출 현황</h3>
          <span style={{ fontSize: 12, color: 'var(--ink-3)' }}>4월 마감 기준 · 8개 지점</span>
        </div>
        <WsBtn variant="bare" size="sm" icon={<I.ChevronRight size={14}/>}>전체 보기</WsBtn>
      </div>
      <div style={{ overflow: 'hidden', borderTop: '1px solid var(--border)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ fontSize: 11.5, color: 'var(--ink-3)', fontWeight: 600, background: 'var(--surface-2)' }}>
              {['지점', '회원', '매출', '비용', '추이', '정산 상태'].map((h, i) => (
                <th key={i} style={{ textAlign: i === 0 ? 'left' : i >= 4 ? 'center' : 'right', padding: '10px 14px', fontWeight: 600, letterSpacing: '-0.005em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((b, i) => (
              <tr key={b.id} style={{ borderTop: i === 0 ? 'none' : '1px solid var(--border)' }}>
                <td style={{ padding: 'var(--pad-cell)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ width: 28, height: 28, borderRadius: 7, background: 'var(--surface-2)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: 'var(--ink-2)', letterSpacing: '-0.01em' }}>{b.name.slice(0,2)}</span>
                    <div>
                      <div style={{ fontWeight: 600, letterSpacing: '-0.01em' }}>{b.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--ink-3)' }} className="ws-mono">{b.code} · {b.region}</div>
                    </div>
                  </div>
                </td>
                <td style={{ textAlign: 'right', padding: 'var(--pad-cell)' }} className="ws-tnum">{b.members.toLocaleString()}</td>
                <td style={{ textAlign: 'right', padding: 'var(--pad-cell)', fontWeight: 600 }} className="ws-tnum">
                  {wsKRW(b.revenue)}
                  <div style={{ marginTop: 2 }}><WsDelta value={b.delta}/></div>
                </td>
                <td style={{ textAlign: 'right', padding: 'var(--pad-cell)' }} className="ws-tnum">{wsKRW(b.costs)}</td>
                <td style={{ padding: 'var(--pad-cell)', width: 88 }}>
                  <div style={{ height: 28 }}><MiniArea data={b.trend} color={b.delta >= 0 ? 'var(--pos)' : 'var(--laon-red)'} height={28}/></div>
                </td>
                <td style={{ textAlign: 'center', padding: 'var(--pad-cell)' }}>
                  <SettleStatus s={b.settled}/>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </WsCard>
  );
}

function SettleStatus({ s }) {
  const map = {
    paid:    { tone: 'pos',  label: '완료',  dot: true },
    pending: { tone: 'warn', label: '진행 중', dot: true },
    overdue: { tone: 'red',  label: '연체',  dot: true },
  };
  const v = map[s] || map.pending;
  return <WsTag tone={v.tone} dot>{v.label}</WsTag>;
}

function AlertsCard({ data }) {
  const tones = { high: 'red', medium: 'warn', low: 'info' };
  return (
    <WsCard padded={false} style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '18px 22px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, letterSpacing: '-0.015em' }}>주의가 필요한 항목</h3>
          <span style={{ fontSize: 12, color: 'var(--ink-3)' }}>지난 24시간 · {data.length}건</span>
        </div>
        <span style={{ width: 28, height: 28, borderRadius: 999, background: 'var(--neg-soft)', color: 'var(--laon-red)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 12 }}>{data.length}</span>
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {data.map((a, i) => (
          <div key={a.id} style={{ padding: '14px 22px', borderTop: i === 0 ? 'none' : '1px solid var(--border)', display: 'flex', gap: 12 }}>
            <WsTag tone={tones[a.severity]} dot>{a.severity === 'high' ? '높음' : a.severity === 'medium' ? '중간' : '낮음'}</WsTag>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13.5, fontWeight: 600, letterSpacing: '-0.01em' }}>{a.title}</div>
              <div style={{ fontSize: 12, color: 'var(--ink-2)', marginTop: 2 }}>{a.desc}</div>
              <div style={{ fontSize: 11, color: 'var(--ink-3)', marginTop: 4 }}>{a.when}</div>
            </div>
            <button style={{ border: 0, background: 'transparent', color: 'var(--ink-3)', cursor: 'pointer' }}><I.ChevronRight size={16}/></button>
          </div>
        ))}
        <div style={{ padding: '12px 22px', marginTop: 'auto', borderTop: '1px solid var(--border)', textAlign: 'center' }}>
          <a href="#" style={{ fontSize: 12.5, color: 'var(--ink-2)', textDecoration: 'none', fontWeight: 600 }}>모든 알림 보기 →</a>
        </div>
      </div>
    </WsCard>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Variant B — 지점 중심 (Branch grid)
// ──────────────────────────────────────────────────────────────────────
function DashboardB({ width = 1440, height = 900, sidebarCollapsed = false, chartType = 'area' }) {
  const d = window.wsData;
  return (
    <DesktopShell width={width} height={height} active="branch" sidebarCollapsed={sidebarCollapsed}
      topbar={
        <WsTopbar
          title="지점 현황"
          breadcrumbs={['WebSettle', '지점 관리']}
          right={
            <>
              <PeriodChip/>
              <WsBtn variant="ghost" size="md" icon={<I.Filter size={15}/>}>필터</WsBtn>
              <WsBtn variant="red" size="md" icon={<I.Download size={15}/>}>정산서 PDF</WsBtn>
            </>
          }
        />
      }
    >
      {/* Top summary band */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--gap-grid)', marginBottom: 'var(--gap-grid)' }}>
        <WsCard style={{ background: 'var(--ink)', color: '#F5F1ED' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: 12.5, opacity: 0.6, fontWeight: 500 }}>전체 매출</div>
              <div style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.025em', marginTop: 8 }}><span className="ws-tnum">19.56</span> <span style={{ fontSize: 14, opacity: 0.6 }}>억 원</span></div>
              <div style={{ display: 'flex', gap: 12, marginTop: 10 }}>
                <span style={{ fontSize: 12, color: '#7CE7AC', fontWeight: 600 }}>+13.7%</span>
                <span style={{ fontSize: 12, opacity: 0.55 }}>vs 3월</span>
              </div>
            </div>
            <div style={{ width: 110, height: 48 }}><MiniArea data={d.monthly.revenue} color="#fff" height={48}/></div>
          </div>
        </WsCard>
        <WsCard>
          <div style={{ fontSize: 12.5, color: 'var(--ink-3)', fontWeight: 500 }}>최고 실적 지점</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
            <span style={{ width: 36, height: 36, borderRadius: 9, background: 'var(--laon-red)', color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 13 }}>GN</span>
            <div>
              <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: '-0.015em' }}>강남 본점</div>
              <div style={{ fontSize: 11.5, color: 'var(--ink-3)' }} className="ws-mono">GN-01 · 서울</div>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
            <div>
              <div style={{ fontSize: 11, color: 'var(--ink-3)' }}>매출</div>
              <div className="ws-tnum" style={{ fontSize: 16, fontWeight: 700 }}>{wsKRW(384200000)}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--ink-3)' }}>회원</div>
              <div className="ws-tnum" style={{ fontSize: 16, fontWeight: 700 }}>1,842</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--ink-3)' }}>증감</div>
              <div style={{ fontSize: 16, fontWeight: 700 }}><WsDelta value={8.2} big/></div>
            </div>
          </div>
        </WsCard>
        <WsCard>
          <div style={{ fontSize: 12.5, color: 'var(--ink-3)', fontWeight: 500 }}>점검 필요 지점</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
            <span style={{ width: 36, height: 36, borderRadius: 9, background: 'var(--neg-soft)', color: 'var(--laon-red)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 13 }}>HD</span>
            <div>
              <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: '-0.015em' }}>해운대점</div>
              <div style={{ fontSize: 11.5, color: 'var(--ink-3)' }} className="ws-mono">HD-06 · 부산</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
            <WsTag tone="red" dot>정산 연체</WsTag>
            <WsTag tone="warn">매출 -8.4%</WsTag>
          </div>
        </WsCard>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700, letterSpacing: '-0.015em' }}>전체 지점 · 8</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <SegPills items={['전체','서울','경기','인천','부산','대전','대구']} active="전체"/>
          <SegPills items={['카드 보기','목록 보기']} active="카드 보기"/>
        </div>
      </div>

      {/* Branch grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--gap-grid)' }}>
        {d.branches.map((b) => <BranchCard key={b.id} b={b}/>)}
      </div>
    </DesktopShell>
  );
}

function BranchCard({ b }) {
  const profit = b.revenue - b.costs;
  const margin = (profit / b.revenue * 100);
  const colors = ['#E60028', '#1F1B1B', '#3963A8', '#2E7D5B', '#B86E1F', '#7340B7', '#5B5450', '#9A918C'];
  const c = colors[b.id.charCodeAt(0) % colors.length];
  return (
    <WsCard hover style={{ display: 'flex', flexDirection: 'column', gap: 14, position: 'relative' }}>
      <div style={{ position: 'absolute', top: 14, right: 14 }}>
        <SettleStatus s={b.settled}/>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ width: 40, height: 40, borderRadius: 10, background: c, color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 13, letterSpacing: '-0.01em' }}>{b.name.slice(0,2)}</span>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: '-0.015em' }}>{b.name}</div>
          <div style={{ fontSize: 11.5, color: 'var(--ink-3)' }} className="ws-mono">{b.code} · {b.region}</div>
        </div>
      </div>
      <div>
        <div style={{ fontSize: 11, color: 'var(--ink-3)' }}>4월 매출</div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
          <span className="ws-tnum" style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }}>{wsKRW(b.revenue)}</span>
          <WsDelta value={b.delta}/>
        </div>
      </div>
      <div style={{ height: 36 }}><MiniArea data={b.trend} color={b.delta >= 0 ? 'var(--ink)' : 'var(--laon-red)'} height={36}/></div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
        <div>
          <div style={{ color: 'var(--ink-3)' }}>회원</div>
          <div className="ws-tnum" style={{ fontWeight: 600, marginTop: 2 }}>{b.members.toLocaleString()}</div>
        </div>
        <div>
          <div style={{ color: 'var(--ink-3)' }}>이익률</div>
          <div className="ws-tnum" style={{ fontWeight: 600, marginTop: 2, color: margin >= 50 ? 'var(--pos)' : 'var(--ink)' }}>{margin.toFixed(1)}%</div>
        </div>
        <div>
          <div style={{ color: 'var(--ink-3)' }}>순이익</div>
          <div className="ws-tnum" style={{ fontWeight: 600, marginTop: 2 }}>{wsKRW(profit)}</div>
        </div>
      </div>
    </WsCard>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Variant C — 재무/손익 (P&L) 중심
// ──────────────────────────────────────────────────────────────────────
function DashboardC({ width = 1440, height = 900, sidebarCollapsed = false, chartType = 'area' }) {
  const d = window.wsData;
  return (
    <DesktopShell width={width} height={height} active="finance" sidebarCollapsed={sidebarCollapsed}
      topbar={
        <WsTopbar
          title="재무 · 손익 (P&L)"
          breadcrumbs={['WebSettle', '재무/회계']}
          right={
            <>
              <PeriodChip/>
              <WsBtn variant="ghost" size="md" icon={<I.Print size={15}/>}>인쇄</WsBtn>
              <WsBtn variant="red" size="md" icon={<I.Doc size={15}/>}>정산서</WsBtn>
            </>
          }
        />
      }
    >
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 'var(--gap-grid)' }}>
        {/* P&L flow */}
        <WsCard>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 12.5, color: 'var(--ink-3)', fontWeight: 500 }}>4월 손익 요약</div>
              <h3 style={{ margin: '4px 0 0', fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em' }}>매출에서 순이익까지</h3>
            </div>
            <WsTag tone="pos" dot>전월 대비 +19.4%</WsTag>
          </div>
          <PnLFlow/>
        </WsCard>

        {/* margin gauge */}
        <WsCard style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 12.5, color: 'var(--ink-3)', fontWeight: 500 }}>이익률</div>
              <h3 style={{ margin: '4px 0 0', fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em' }}>52.3%</h3>
            </div>
            <SegPills items={['월', '분기', '연']} active="월"/>
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: 8 }}>
            <Donut
              segments={[
                { label: '순이익', value: 52.3, color: 'var(--laon-red)' },
                { label: '비용',   value: 47.7, color: 'var(--surface-3)' },
              ]}
              size={180} thickness={26}
              center={<>
                <span className="ws-tnum" style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.025em' }}>52.3%</span>
                <span style={{ fontSize: 11, color: 'var(--pos)', fontWeight: 600, marginTop: 2 }}>+4.1%p</span>
                <span style={{ fontSize: 10.5, color: 'var(--ink-3)' }}>전월 대비</span>
              </>}
            />
          </div>
        </WsCard>
      </div>

      {/* P&L table & expense bars */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--gap-grid)', marginTop: 'var(--gap-grid)' }}>
        <WsCard padded={false}>
          <div style={{ padding: '18px 22px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, letterSpacing: '-0.015em' }}>손익 계산서 (요약)</h3>
            <WsBtn variant="bare" size="sm">자세히</WsBtn>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: 'var(--surface-2)', fontSize: 11.5, color: 'var(--ink-3)' }}>
                <th style={{ textAlign: 'left', padding: '10px 14px', fontWeight: 600 }}>항목</th>
                <th style={{ textAlign: 'right', padding: '10px 14px', fontWeight: 600 }}>3월</th>
                <th style={{ textAlign: 'right', padding: '10px 14px', fontWeight: 600 }}>4월</th>
                <th style={{ textAlign: 'right', padding: '10px 14px', fontWeight: 600 }}>증감</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['매출액',        1720000000, 1956000000,  true],
                ['  └ 회원권',    1102000000, 1248000000,  true],
                ['  └ PT/레슨',    412000000,  482000000,  true],
                ['  └ 부대수익',   206000000,  226000000,  true],
                ['매출원가',      -488000000, -512000000,  false],
                ['매출총이익',    1232000000, 1444000000,  true,  true],
                ['판관비',        -376000000, -421000000,  false],
                ['영업이익',       856000000, 1023000000,  true,  true],
                ['순이익',         703000000,  847000000,  true,  true],
              ].map(([label, prev, cur, up, bold], i) => {
                const delta = ((cur - prev) / Math.abs(prev) * 100);
                return (
                  <tr key={i} style={{ borderTop: '1px solid var(--border)', fontWeight: bold ? 700 : 500, background: bold ? 'var(--surface-2)' : 'transparent' }}>
                    <td style={{ padding: 'var(--pad-cell)', whiteSpace: 'pre' }}>{label}</td>
                    <td style={{ padding: 'var(--pad-cell)', textAlign: 'right' }} className="ws-tnum">{wsKRW(prev)}</td>
                    <td style={{ padding: 'var(--pad-cell)', textAlign: 'right' }} className="ws-tnum">{wsKRW(cur)}</td>
                    <td style={{ padding: 'var(--pad-cell)', textAlign: 'right', color: delta >= 0 ? 'var(--pos)' : 'var(--neg)' }} className="ws-tnum">{wsPct(delta)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </WsCard>
        <WsCard>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 12.5, color: 'var(--ink-3)', fontWeight: 500 }}>비용 분포</div>
              <h3 style={{ margin: '4px 0 0', fontSize: 16, fontWeight: 700, letterSpacing: '-0.015em' }}>4월 933M 원</h3>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {d.expenses.map((e, i) => {
              const total = d.expenses.reduce((a, x) => a + x.value, 0);
              const pct = (e.value / total) * 100;
              return (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 5 }}>
                    <span style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--ink-2)' }}>{e.label}</span>
                    <span style={{ fontSize: 12, color: 'var(--ink-3)' }} className="ws-tnum">{wsKRW(e.value)} <span style={{ marginLeft: 6 }}>{pct.toFixed(1)}%</span></span>
                  </div>
                  <div style={{ height: 6, background: 'var(--surface-2)', borderRadius: 999, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: e.color, borderRadius: 999, transition: 'width .3s' }}/>
                  </div>
                </div>
              );
            })}
          </div>
        </WsCard>
      </div>
    </DesktopShell>
  );
}

function PnLFlow() {
  // Sankey-ish horizontal flow
  const items = [
    { label: '매출액', value: 1956, color: 'var(--ink)', width: '100%' },
    { label: '매출원가', value: -512, color: 'var(--ink-3)', sub: '-26.2%' },
    { label: '매출총이익', value: 1444, color: 'var(--ink)', width: '73.8%' },
    { label: '판관비',   value: -421, color: 'var(--ink-3)', sub: '-21.5%' },
    { label: '영업이익', value: 1023, color: 'var(--laon-red)', width: '52.3%' },
    { label: '법인세 외', value: -176, color: 'var(--ink-3)', sub: '-9.0%' },
    { label: '순이익',  value: 847, color: 'var(--pos)', width: '43.3%' },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {items.map((it, i) => {
        const w = it.width || (Math.abs(it.value) / 1956 * 100 + '%');
        const isNeg = it.value < 0;
        return (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 100, fontSize: 12.5, color: 'var(--ink-2)', fontWeight: 500, flexShrink: 0 }}>{it.label}</div>
            <div style={{ flex: 1, height: 26, background: 'var(--surface-2)', borderRadius: 7, overflow: 'hidden', position: 'relative' }}>
              <div style={{
                height: '100%', width: w, background: it.color, borderRadius: 7,
                display: 'flex', alignItems: 'center', justifyContent: isNeg ? 'flex-start' : 'flex-end',
                padding: '0 10px',
                opacity: isNeg ? 0.6 : 1,
              }}>
                <span style={{ fontSize: 11.5, fontWeight: 700, color: ['var(--ink)', 'var(--ink-3)'].includes(it.color) ? '#fff' : '#fff', whiteSpace: 'nowrap' }}>
                  {it.value > 0 ? '+' : ''}{it.value}M {it.sub && <span style={{ opacity: 0.7, marginLeft: 6 }}>{it.sub}</span>}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Settlement detail with side drawer
// ──────────────────────────────────────────────────────────────────────
function ScreenSettlement({ width = 1440, height = 900, sidebarCollapsed = false }) {
  const d = window.wsData;
  const [drawerOpen, setDrawerOpen] = dUseState(true);
  const [selected, setSelected] = dUseState(d.payments[2]); // 최유나, 2.4M

  return (
    <DesktopShell width={width} height={height} active="settlement" sidebarCollapsed={sidebarCollapsed}
      topbar={
        <WsTopbar
          title="정산 · 매출 상세"
          breadcrumbs={['WebSettle', '정산/매출', '2026년 4월']}
          right={
            <>
              <PeriodChip/>
              <WsBtn variant="ghost" size="md" icon={<I.Filter size={15}/>}>필터</WsBtn>
              <WsBtn variant="red" size="md" icon={<I.Download size={15}/>}>PDF 출력</WsBtn>
            </>
          }
        />
      }
    >
      {/* Summary band */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 18 }}>
        {[
          ['총 결제 건수', '2,184', '건', 4.1],
          ['총 결제액', '19.56', '억', 13.7],
          ['환불액', '42.8', '백만', -4.2],
          ['평균 결제액', '89.6', '만', 9.2],
        ].map(([l, v, u, dlt], i) => (
          <div key={i} style={{ padding: 16, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12 }}>
            <div style={{ fontSize: 11.5, color: 'var(--ink-3)', fontWeight: 500 }}>{l}</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginTop: 6 }}>
              <span className="ws-tnum" style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.025em' }}>{v}</span>
              <span style={{ fontSize: 12, color: 'var(--ink-3)' }}>{u}</span>
              <span style={{ marginLeft: 'auto' }}><WsDelta value={dlt}/></span>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 14, flexWrap: 'wrap' }}>
        <SegPills items={['전체', '카드', '계좌이체', '현장결제']} active="전체"/>
        <span style={{ width: 1, height: 22, background: 'var(--border)', margin: '0 4px' }}/>
        <SegPills items={['전체 상태', '성공', '진행 중', '환불']} active="전체 상태"/>
        <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--ink-3)' }}>총 2,184건 · 8건 표시</span>
      </div>

      {/* Table */}
      <WsCard padded={false}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
          <thead>
            <tr style={{ fontSize: 11.5, color: 'var(--ink-3)', fontWeight: 600, background: 'var(--surface-2)' }}>
              <th style={th(40)}><Checkbox/></th>
              <th style={{ ...th(), textAlign: 'left' }}>거래 ID</th>
              <th style={{ ...th(), textAlign: 'left' }}>일시</th>
              <th style={{ ...th(), textAlign: 'left' }}>지점</th>
              <th style={{ ...th(), textAlign: 'left' }}>회원</th>
              <th style={{ ...th(), textAlign: 'left' }}>유형</th>
              <th style={{ ...th(), textAlign: 'left' }}>결제수단</th>
              <th style={{ ...th(), textAlign: 'right' }}>금액</th>
              <th style={{ ...th(), textAlign: 'center' }}>상태</th>
              <th style={th(40)}></th>
            </tr>
          </thead>
          <tbody>
            {d.payments.map((p, i) => {
              const isSel = selected?.id === p.id;
              return (
                <tr key={p.id}
                  onClick={() => { setSelected(p); setDrawerOpen(true); }}
                  style={{ borderTop: '1px solid var(--border)', cursor: 'pointer', background: isSel ? 'var(--neg-soft)' : 'transparent' }}>
                  <td style={td()}><Checkbox/></td>
                  <td style={td()} className="ws-mono"><span style={{ color: 'var(--ink-2)' }}>{p.id}</span></td>
                  <td style={td()} className="ws-tnum">{p.ts.slice(5)}</td>
                  <td style={td()}>{p.branch}</td>
                  <td style={td()}><div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Avatar name={p.member} size={22}/>{p.member}</div></td>
                  <td style={td()}>{p.type}</td>
                  <td style={td()}><WsTag tone="neutral">{p.method}</WsTag></td>
                  <td style={{ ...td(), textAlign: 'right', fontWeight: 700 }} className="ws-tnum">
                    {p.status === 'refunded' && '−'}{p.amount.toLocaleString()} 원
                  </td>
                  <td style={{ ...td(), textAlign: 'center' }}>
                    <PaymentStatus s={p.status}/>
                  </td>
                  <td style={td()}>
                    <I.ChevronRight size={14} style={{ color: 'var(--ink-3)' }}/>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </WsCard>

      <Drawer open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <PaymentDrawerBody p={selected} onClose={() => setDrawerOpen(false)}/>
      </Drawer>
    </DesktopShell>
  );
}

const th = (w) => ({ padding: '10px 14px', fontWeight: 600, letterSpacing: '-0.005em', width: w });
const td = () => ({ padding: 'var(--pad-cell)' });

function Checkbox({ checked = false }) {
  return (
    <span style={{
      width: 16, height: 16, borderRadius: 4,
      background: checked ? 'var(--ink)' : 'var(--surface)',
      border: '1.4px solid ' + (checked ? 'var(--ink)' : 'var(--border-strong)'),
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
    }}>{checked && <I.Check size={11} sw={3}/>}</span>
  );
}

function PaymentStatus({ s }) {
  const map = {
    success:  { tone: 'pos',  label: '성공' },
    pending:  { tone: 'warn', label: '진행 중' },
    refunded: { tone: 'red',  label: '환불' },
  };
  const v = map[s] || map.pending;
  return <WsTag tone={v.tone} dot>{v.label}</WsTag>;
}

function PaymentDrawerBody({ p, onClose }) {
  if (!p) return null;
  return (
    <>
      <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1 }}>
          <div className="ws-mono" style={{ fontSize: 12, color: 'var(--ink-3)' }}>{p.id}</div>
          <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: '-0.02em', marginTop: 2 }}>거래 상세</div>
        </div>
        <button onClick={onClose} style={iconBtn}><I.X size={16}/></button>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '24px 24px 16px' }}>
        <div style={{ background: 'var(--surface-2)', padding: 16, borderRadius: 12, marginBottom: 22 }}>
          <div style={{ fontSize: 11.5, color: 'var(--ink-3)', fontWeight: 500 }}>결제 금액</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 6 }}>
            <span className="ws-tnum" style={{ fontSize: 34, fontWeight: 700, letterSpacing: '-0.03em' }}>{p.amount.toLocaleString()}</span>
            <span style={{ fontSize: 14, color: 'var(--ink-2)', fontWeight: 600 }}>원</span>
          </div>
          <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
            <PaymentStatus s={p.status}/>
            <WsTag tone="neutral">{p.method}</WsTag>
            <WsTag tone="neutral">{p.type}</WsTag>
          </div>
        </div>

        <Section title="결제 정보">
          <KV k="거래 시간" v={p.ts}/>
          <KV k="결제 수단" v={`${p.method} · KB국민카드 **34`}/>
          <KV k="승인 번호" v="0028471" mono/>
          <KV k="PG사" v="토스페이먼츠"/>
          <KV k="할부 개월" v="일시불"/>
        </Section>

        <Section title="회원 정보">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0' }}>
            <Avatar name={p.member} size={36}/>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>{p.member} <span style={{ color: 'var(--ink-3)', fontWeight: 500, fontSize: 12 }}>· M-2023-0184</span></div>
              <div style={{ fontSize: 12, color: 'var(--ink-3)', marginTop: 2 }}>VIP · 가입 28개월차</div>
            </div>
            <WsBtn variant="bare" size="sm" icon={<I.ChevronRight size={14}/>}>프로필</WsBtn>
          </div>
        </Section>

        <Section title="지점/담당자">
          <KV k="지점" v={p.branch + ' · BD-02'}/>
          <KV k="담당 매니저" v="박상우 점장"/>
          <KV k="결제 채널" v="키오스크"/>
        </Section>

        <Section title="정산 상태">
          <div style={{ padding: '10px 0' }}>
            <SettleTimeline/>
          </div>
        </Section>
      </div>

      <div style={{ padding: '12px 24px', borderTop: '1px solid var(--border)', display: 'flex', gap: 8, background: 'var(--surface)' }}>
        <WsBtn variant="ghost" size="md" style={{ flex: 1 }} icon={<I.Print size={15}/>}>영수증</WsBtn>
        <WsBtn variant="ghost" size="md" style={{ flex: 1 }} icon={<I.Refund size={15}/>}>환불</WsBtn>
        <WsBtn variant="primary" size="md" style={{ flex: 1 }} icon={<I.Doc size={15}/>}>정산서</WsBtn>
      </div>
    </>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ fontSize: 11, color: 'var(--ink-3)', fontWeight: 700, letterSpacing: '0.06em', marginBottom: 8 }}>{title.toUpperCase()}</div>
      <div>{children}</div>
    </div>
  );
}

function KV({ k, v, mono = false }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px dashed var(--border)', fontSize: 13 }}>
      <span style={{ color: 'var(--ink-3)' }}>{k}</span>
      <span style={{ color: 'var(--ink)', fontWeight: 500 }} className={mono ? 'ws-mono' : ''}>{v}</span>
    </div>
  );
}

function SettleTimeline() {
  const steps = [
    { label: '결제 승인',  date: '04/22 13:58', done: true },
    { label: '검토 완료',  date: '04/22 14:30', done: true },
    { label: '정산 예정',  date: '04/30',        done: true, active: true },
    { label: '입금 완료',  date: '05/02 (예정)', done: false },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {steps.map((s, i) => (
        <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
          <div style={{ position: 'relative', width: 18 }}>
            <span style={{
              width: 14, height: 14, borderRadius: 999,
              background: s.done ? (s.active ? 'var(--laon-red)' : 'var(--ink)') : 'var(--surface-2)',
              border: '2px solid ' + (s.done ? (s.active ? 'var(--laon-red)' : 'var(--ink)') : 'var(--border-strong)'),
              display: 'inline-block',
            }}/>
            {i !== steps.length - 1 && <span style={{ position: 'absolute', left: 6, top: 16, width: 2, height: 24, background: s.done ? 'var(--ink)' : 'var(--border)' }}/>}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: s.active ? 600 : 500, color: s.done ? 'var(--ink)' : 'var(--ink-3)' }}>{s.label}</div>
            <div style={{ fontSize: 11.5, color: 'var(--ink-3)' }}>{s.date}</div>
          </div>
          {s.active && <WsTag tone="red" dot>대기 중</WsTag>}
        </div>
      ))}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Reports screen
// ──────────────────────────────────────────────────────────────────────
function ScreenReports({ width = 1440, height = 900, sidebarCollapsed = false, chartType = 'area' }) {
  const d = window.wsData;
  return (
    <DesktopShell width={width} height={height} active="reports" sidebarCollapsed={sidebarCollapsed}
      topbar={
        <WsTopbar
          title="리포트 · 기간 분석"
          breadcrumbs={['WebSettle', '리포트']}
          right={
            <>
              <SegPills items={['주간','월간','분기','연간']} active="월간"/>
              <PeriodChip value="2026년 4월 → 5월"/>
              <WsBtn variant="ghost" size="md" icon={<I.Download size={15}/>}>내보내기</WsBtn>
              <WsBtn variant="red" size="md" icon={<I.Print size={15}/>}>인쇄</WsBtn>
            </>
          }
        />
      }
    >
      {/* Top KPIs (dense) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12, marginBottom: 'var(--gap-grid)' }}>
        {[
          ['총 매출',  '19.56', '억', 13.7, 'red'],
          ['순이익', '10.23', '억', 19.4, 'pos'],
          ['이익률', '52.3', '%', 4.1, 'pos'],
          ['ARPU',  '227', '천', 5.2, 'pos'],
          ['LTV',   '4.86', '백만', 8.1, 'pos'],
          ['CAC',   '92', '천', -3.4, 'pos'],
        ].map(([l, v, u, dlt, t], i) => (
          <div key={i} style={{ padding: 14, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 11 }}>
            <div style={{ fontSize: 11, color: 'var(--ink-3)', fontWeight: 500 }}>{l}</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 3, marginTop: 6 }}>
              <span className="ws-tnum" style={{ fontSize: 19, fontWeight: 700, letterSpacing: '-0.02em' }}>{v}</span>
              <span style={{ fontSize: 11, color: 'var(--ink-3)' }}>{u}</span>
            </div>
            <div style={{ marginTop: 4 }}><WsDelta value={dlt}/></div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 'var(--gap-grid)' }}>
        <WsCard>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 12.5, color: 'var(--ink-3)' }}>일별 매출</div>
              <h3 style={{ margin: '4px 0 0', fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em' }}>4월 전체 흐름</h3>
            </div>
            <ChartLegend items={[
              { label: '매출', color: 'var(--ink)' },
              { label: '이전 달', color: 'var(--ink-4)' },
            ]}/>
          </div>
          <ChartArea
            chartType={chartType}
            height={220}
            labels={['1', '4', '8', '12', '16', '20', '24', '28', '30']}
            series={[
              { name: '이전 달', values: [52,58,64,72,80,78,84,90,86].map(v => v * 1e6), color: 'var(--ink-4)' },
              { name: '매출',    values: [58,64,76,82,86,94,102,108,112].map(v => v * 1e6), color: 'var(--ink)' },
            ]}
          />
        </WsCard>

        <WsCard>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 12.5, color: 'var(--ink-3)' }}>지점별 기여도</div>
              <h3 style={{ margin: '4px 0 0', fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em' }}>매출 점유</h3>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {d.branches.slice(0, 6).map((b, i) => {
              const total = d.branches.reduce((a, x) => a + x.revenue, 0);
              const pct = b.revenue / total * 100;
              return (
                <div key={b.id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
                    <span style={{ fontSize: 12.5, fontWeight: 500 }}>{b.name}</span>
                    <span className="ws-tnum" style={{ fontSize: 11.5, color: 'var(--ink-3)' }}>{pct.toFixed(1)}% · {wsKRW(b.revenue)}</span>
                  </div>
                  <div style={{ height: 7, background: 'var(--surface-2)', borderRadius: 999 }}>
                    <div style={{ height: '100%', width: pct + '%', background: i === 0 ? 'var(--laon-red)' : 'var(--ink)', borderRadius: 999 }}/>
                  </div>
                </div>
              );
            })}
          </div>
        </WsCard>
      </div>

      {/* Heatmap & top members */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 'var(--gap-grid)', marginTop: 'var(--gap-grid)' }}>
        <WsCard>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 12.5, color: 'var(--ink-3)' }}>요일·시간대 매출 히트맵</div>
              <h3 style={{ margin: '4px 0 0', fontSize: 16, fontWeight: 700, letterSpacing: '-0.015em' }}>피크 타임 분석</h3>
            </div>
            <ChartLegend items={[
              { label: '낮음', color: 'var(--surface-3)' },
              { label: '높음', color: 'var(--laon-red)' },
            ]}/>
          </div>
          <Heatmap/>
        </WsCard>
        <WsCard padded={false}>
          <div style={{ padding: '18px 22px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, letterSpacing: '-0.015em' }}>VIP 결제 TOP 5</h3>
              <span style={{ fontSize: 12, color: 'var(--ink-3)' }}>4월 누적 기준</span>
            </div>
            <WsBtn variant="bare" size="sm">전체 보기</WsBtn>
          </div>
          <div>
            {[
              ['이서연', '강남 본점', 4280000],
              ['최유나', '분당점',    3940000],
              ['박지훈', '잠실점',    3620000],
              ['한지민', '강남 본점', 3460000],
              ['윤서아', '해운대점',  3120000],
            ].map(([name, branch, amt], i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 22px', borderTop: '1px solid var(--border)' }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--ink-3)', width: 18 }} className="ws-mono">{String(i+1).padStart(2,'0')}</span>
                <Avatar name={name} size={32}/>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{name}</div>
                  <div style={{ fontSize: 11.5, color: 'var(--ink-3)' }}>{branch}</div>
                </div>
                <span className="ws-tnum" style={{ fontSize: 13, fontWeight: 700 }}>{amt.toLocaleString()} 원</span>
              </div>
            ))}
          </div>
        </WsCard>
      </div>
    </DesktopShell>
  );
}

function Heatmap() {
  const days = ['월', '화', '수', '목', '금', '토', '일'];
  const hours = ['06','08','10','12','14','16','18','20','22'];
  // pseudo deterministic data
  const data = days.map((d, di) => hours.map((h, hi) => {
    const v = Math.abs(Math.sin(di * 1.3 + hi * 0.6)) * 0.6
             + (hi > 2 && hi < 6 ? 0.3 : 0)
             + (di >= 5 ? 0.15 : 0)
             + (hi >= 7 ? 0.2 : 0);
    return Math.min(1, v);
  }));
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '24px repeat(9, 1fr)', gap: 4 }}>
      <div/>
      {hours.map(h => <div key={h} style={{ fontSize: 10, color: 'var(--ink-3)', textAlign: 'center' }}>{h}</div>)}
      {days.map((d, di) => (
        <React.Fragment key={d}>
          <div style={{ fontSize: 11, color: 'var(--ink-3)', display: 'flex', alignItems: 'center' }}>{d}</div>
          {data[di].map((v, hi) => (
            <div key={hi} style={{
              aspectRatio: '1.4 / 1',
              borderRadius: 4,
              background: `color-mix(in oklch, var(--laon-red) ${v * 90}%, var(--surface-3))`,
              opacity: 0.95,
            }}/>
          ))}
        </React.Fragment>
      ))}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  PDF Settlement preview (modal-style fullscreen artboard)
// ──────────────────────────────────────────────────────────────────────
function ScreenSettlementPDF({ width = 1440, height = 900, sidebarCollapsed = false }) {
  return (
    <DesktopShell width={width} height={height} active="settlement" sidebarCollapsed={sidebarCollapsed}
      topbar={
        <WsTopbar
          title="정산서 미리보기"
          breadcrumbs={['WebSettle', '정산/매출', '2026년 4월', '정산서']}
          right={
            <>
              <WsBtn variant="ghost" size="md" icon={<I.Mail size={15}/>}>이메일</WsBtn>
              <WsBtn variant="ghost" size="md" icon={<I.Print size={15}/>}>인쇄</WsBtn>
              <WsBtn variant="red" size="md" icon={<I.Download size={15}/>}>PDF 다운로드</WsBtn>
            </>
          }
        />
      }
    >
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 'var(--gap-grid)' }}>
        {/* PDF Page */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div style={{
            width: 760,
            background: '#fff', color: '#111',
            border: '1px solid var(--border)', borderRadius: 6,
            boxShadow: 'var(--shadow-md)',
            padding: '56px 56px 48px',
            fontFamily: 'var(--font-sans)',
            position: 'relative',
          }}>
            <div style={{ position: 'absolute', top: 24, right: 24, fontSize: 10, color: '#888', letterSpacing: '0.06em' }} className="ws-mono">PAGE 1 / 3</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
              <div>
                <div style={{ fontSize: 11, color: '#888', letterSpacing: '0.12em', fontWeight: 700 }}>정산서 · SETTLEMENT STATEMENT</div>
                <h1 style={{ fontSize: 30, fontWeight: 800, margin: '8px 0 4px', letterSpacing: '-0.025em', color: '#111' }}>2026년 4월 정산내역</h1>
                <div style={{ fontSize: 12, color: '#555' }}>정산 기간: 2026-04-01 → 2026-04-30 · 발행일: 2026-05-02</div>
              </div>
              <img src="assets/laon-logo.png" alt="LAON SPORTS" style={{ height: 28 }}/>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 22, marginBottom: 26, fontSize: 11.5 }}>
              <div>
                <div style={{ color: '#777', fontWeight: 700, fontSize: 10, letterSpacing: '0.08em', marginBottom: 8 }}>공급자</div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>(주)라온스포츠</div>
                <div style={{ color: '#444', marginTop: 3, lineHeight: 1.5 }}>
                  대표: 김상호 · 사업자등록번호: 220-86-12345<br/>
                  서울 강남구 테헤란로 152, 11F · 02-528-0000
                </div>
              </div>
              <div>
                <div style={{ color: '#777', fontWeight: 700, fontSize: 10, letterSpacing: '0.08em', marginBottom: 8 }}>정산 대상</div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>분당점 (BD-02)</div>
                <div style={{ color: '#444', marginTop: 3, lineHeight: 1.5 }}>
                  대표: 박상우 · 입금계좌: 신한 110-***-829341<br/>
                  경기 성남시 분당구 정자일로 95, 2F
                </div>
              </div>
            </div>

            {/* Summary */}
            <div style={{ background: '#faf7f5', borderRadius: 6, padding: '16px 20px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
              {[
                ['총 매출', '264,800,000', '원'],
                ['공제 (수수료)', '13,240,000', '원'],
                ['정산 차감', '6,800,000', '원'],
                ['실수령액', '244,760,000', '원', true],
              ].map(([l, v, u, bold], i) => (
                <div key={i}>
                  <div style={{ fontSize: 10, color: '#777', fontWeight: 600, letterSpacing: '0.05em' }}>{l.toUpperCase()}</div>
                  <div style={{ marginTop: 4, color: bold ? '#E60028' : '#111' }} className="ws-tnum">
                    <span style={{ fontSize: bold ? 18 : 15, fontWeight: 700 }}>{v}</span>
                    <span style={{ fontSize: 10, color: '#777', marginLeft: 3 }}>{u}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Line items */}
            <div style={{ color: '#777', fontWeight: 700, fontSize: 10, letterSpacing: '0.08em', marginBottom: 8 }}>매출 상세</div>
            <table style={{ width: '100%', fontSize: 11.5, borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1.5px solid #111', color: '#444', fontWeight: 600 }}>
                  <th style={{ textAlign: 'left', padding: '8px 4px' }}>품목</th>
                  <th style={{ textAlign: 'right', padding: '8px 4px' }}>건수</th>
                  <th style={{ textAlign: 'right', padding: '8px 4px' }}>단가</th>
                  <th style={{ textAlign: 'right', padding: '8px 4px' }}>금액</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['회원권 - 월간', 218, 890000, 194020000],
                  ['회원권 - 연간',  18, 2400000, 43200000],
                  ['PT 30회 패키지', 22, 1200000, 26400000],
                  ['필라테스 그룹',  14,  450000,  6300000],
                  ['부대 - 락커/주차', null, null, -5120000],
                ].map(([item, qty, unit, amt], i) => (
                  <tr key={i} style={{ borderBottom: '1px dashed #ddd' }}>
                    <td style={{ padding: '8px 4px', color: '#222' }}>{item}</td>
                    <td style={{ padding: '8px 4px', textAlign: 'right', color: '#444' }} className="ws-tnum">{qty ? qty.toLocaleString() : '—'}</td>
                    <td style={{ padding: '8px 4px', textAlign: 'right', color: '#444' }} className="ws-tnum">{unit ? unit.toLocaleString() : '—'}</td>
                    <td style={{ padding: '8px 4px', textAlign: 'right', fontWeight: 600 }} className="ws-tnum">{amt.toLocaleString()}</td>
                  </tr>
                ))}
                <tr style={{ borderTop: '1.5px solid #111', fontWeight: 700 }}>
                  <td style={{ padding: '10px 4px' }} colSpan={3}>합계</td>
                  <td style={{ padding: '10px 4px', textAlign: 'right' }} className="ws-tnum">264,800,000</td>
                </tr>
              </tbody>
            </table>

            <div style={{ marginTop: 30, paddingTop: 14, borderTop: '1px solid #eee', fontSize: 10, color: '#888', display: 'flex', justifyContent: 'space-between' }}>
              <span>본 정산서는 WebSettle 2.4.1 에서 자동 생성되었습니다.</span>
              <span className="ws-mono">SETT-202604-BD02</span>
            </div>
          </div>
        </div>

        {/* Side panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <WsCard>
            <div style={{ fontSize: 11, color: 'var(--ink-3)', fontWeight: 700, letterSpacing: '0.06em', marginBottom: 10 }}>출력 옵션</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <RowToggle label="회사 로고 포함" checked/>
              <RowToggle label="QR 검증 코드" checked/>
              <RowToggle label="상세 거래 내역" checked/>
              <RowToggle label="비용 분석 첨부"/>
              <RowToggle label="비밀번호 보호"/>
            </div>
          </WsCard>

          <WsCard>
            <div style={{ fontSize: 11, color: 'var(--ink-3)', fontWeight: 700, letterSpacing: '0.06em', marginBottom: 10 }}>발송</div>
            <div style={{ fontSize: 12.5, color: 'var(--ink-2)', lineHeight: 1.5 }}>
              <div>받는 사람</div>
              <div style={{ marginTop: 6, padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar name="박상우" size={22}/>
                <span style={{ fontSize: 12, fontWeight: 600 }}>박상우 점장</span>
                <span style={{ fontSize: 11, color: 'var(--ink-3)' }} className="ws-mono">bd02@laonsports.com</span>
              </div>
            </div>
            <WsBtn variant="primary" size="md" style={{ width: '100%', marginTop: 12 }} icon={<I.Mail size={15}/>}>이메일로 발송</WsBtn>
          </WsCard>

          <WsCard>
            <div style={{ fontSize: 11, color: 'var(--ink-3)', fontWeight: 700, letterSpacing: '0.06em', marginBottom: 10 }}>이력</div>
            <div style={{ fontSize: 12, color: 'var(--ink-2)', lineHeight: 1.6 }}>
              <div>2026-05-02 · 자동 생성</div>
              <div>2026-05-02 · 김재영 승인</div>
              <div style={{ color: 'var(--ink-3)' }}>—</div>
            </div>
          </WsCard>
        </div>
      </div>
    </DesktopShell>
  );
}

function RowToggle({ label, checked = false }) {
  const [on, set] = dUseState(checked);
  return (
    <button onClick={() => set(!on)} style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10,
      padding: '6px 0', border: 0, background: 'transparent', cursor: 'pointer',
      fontSize: 13, color: 'var(--ink)',
      textAlign: 'left',
    }}>
      <span>{label}</span>
      <span style={{
        width: 32, height: 18, borderRadius: 999,
        background: on ? 'var(--ink)' : 'var(--surface-3)',
        position: 'relative', transition: 'background .15s',
      }}>
        <span style={{
          position: 'absolute', top: 2, left: on ? 16 : 2,
          width: 14, height: 14, borderRadius: 999, background: '#fff',
          transition: 'left .15s',
        }}/>
      </span>
    </button>
  );
}

Object.assign(window, {
  ScreenLogin, DashboardA, DashboardB, DashboardC,
  ScreenSettlement, ScreenReports, ScreenSettlementPDF,
});
