// components.jsx — Shared UI primitives for WebSettle

const { useState, useEffect, useMemo, useRef } = React;
const I = window.Icons;

// ──────────────────────────────────────────────────────────────────────
//  Number / date formatting
// ──────────────────────────────────────────────────────────────────────
const wsKRW = (n, opts = {}) => {
  const { unit = 'auto', sign = false } = opts;
  if (n == null) return '—';
  const abs = Math.abs(n);
  let v = n, s = '원';
  if (unit === 'auto') {
    if (abs >= 1e8) { v = n / 1e8; s = '억'; }
    else if (abs >= 1e4) { v = n / 1e4; s = '만'; }
    else s = '';
  }
  const num = (Math.round(v * 10) / 10).toLocaleString('ko-KR', { maximumFractionDigits: 1 });
  return (sign && n > 0 ? '+' : '') + num + (s ? ' ' + s : '');
};
const wsPct = (n, digits = 1) => `${n > 0 ? '+' : ''}${n.toFixed(digits)}%`;

// ──────────────────────────────────────────────────────────────────────
//  LAON brand mark
// ──────────────────────────────────────────────────────────────────────
function WsLogo({ size = 28, mono = false, withWordmark = true }) {
  // Simplified mark: red rounded square with stylized "L" + "S" cross
  const c = mono ? 'currentColor' : 'var(--laon-red)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <svg width={size} height={size} viewBox="0 0 32 32" style={{ flexShrink: 0 }}>
        <rect x="0" y="0" width="32" height="32" rx="8" fill={c}/>
        <path d="M8 7 v14 h7 v-4 h-3 V7 Z" fill="#fff"/>
        <path d="M17 14 q0 -3 3 -3 h4 v3.2 h-3.5 q-0.8 0 -0.8 .9 q0 .8 .9 .9 l2 .4 q2.5 .5 2.5 3 q0 3 -3 3 h-5 v-3.2 h4.5 q.9 0 .9 -1 q0 -.7 -.9 -.9 l-1.9 -.4 q-2.7 -.6 -2.7 -3 Z" fill="#fff"/>
      </svg>
      {withWordmark && (
        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1 }}>
          <span style={{ fontSize: 15, fontWeight: 800, letterSpacing: '-0.01em', color: 'var(--ink)' }}>WebSettle</span>
          <span style={{ fontSize: 9.5, fontWeight: 500, color: 'var(--ink-3)', marginTop: 3, letterSpacing: '0.06em' }}>LAON SPORTS</span>
        </div>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Primitives
// ──────────────────────────────────────────────────────────────────────
function WsCard({ children, style, padded = true, hover = false, ...rest }) {
  return (
    <div
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 14,
        boxShadow: 'var(--shadow-sm)',
        padding: padded ? 'var(--pad-card)' : 0,
        transition: 'box-shadow .2s, transform .2s',
        ...(hover && { cursor: 'pointer' }),
        ...style,
      }}
      {...rest}
    >
      {children}
    </div>
  );
}

function WsBtn({ variant = 'primary', size = 'md', icon, children, style, ...rest }) {
  const sizes = {
    sm: { fontSize: 12.5, padding: '6px 12px', height: 30, gap: 6 },
    md: { fontSize: 13.5, padding: '8px 16px', height: 36, gap: 7 },
    lg: { fontSize: 14.5, padding: '10px 20px', height: 44, gap: 8 },
  };
  const variants = {
    primary: { background: 'var(--ink)', color: 'var(--bg)', border: '1px solid var(--ink)' },
    red:     { background: 'var(--laon-red)', color: '#fff', border: '1px solid var(--laon-red)' },
    soft:    { background: 'var(--surface-2)', color: 'var(--ink)', border: '1px solid transparent' },
    ghost:   { background: 'transparent', color: 'var(--ink)', border: '1px solid var(--border-strong)' },
    bare:    { background: 'transparent', color: 'var(--ink-2)', border: '1px solid transparent' },
  };
  return (
    <button
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        fontWeight: 600, letterSpacing: '-0.01em', borderRadius: 10,
        whiteSpace: 'nowrap',
        ...sizes[size], ...variants[variant], ...style,
      }}
      {...rest}
    >
      {icon}
      {children}
    </button>
  );
}

function WsTag({ tone = 'neutral', children, style, dot = false }) {
  const tones = {
    neutral: { bg: 'var(--surface-2)', fg: 'var(--ink-2)' },
    red:     { bg: 'var(--neg-soft)', fg: 'var(--neg)' },
    pos:     { bg: 'var(--pos-soft)', fg: 'var(--pos)' },
    warn:    { bg: 'var(--warn-soft)', fg: 'var(--warn)' },
    info:    { bg: 'var(--info-soft)', fg: 'var(--info)' },
  };
  const t = tones[tone];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 9px', borderRadius: 999,
      fontSize: 11.5, fontWeight: 600, letterSpacing: '-0.005em',
      background: t.bg, color: t.fg,
      ...style,
    }}>
      {dot && <span style={{ width: 6, height: 6, borderRadius: 999, background: t.fg }} />}
      {children}
    </span>
  );
}

function WsDelta({ value, suffix = '%', big = false }) {
  const pos = value >= 0;
  const Icon = pos ? I.ArrowUp : I.ArrowDown;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 2,
      color: pos ? 'var(--pos)' : 'var(--neg)',
      fontSize: big ? 13 : 12, fontWeight: 600,
    }}>
      <Icon size={big ? 14 : 12} sw={2.2}/>
      {Math.abs(value).toFixed(1)}{suffix}
    </span>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Sidebar (Desktop)
// ──────────────────────────────────────────────────────────────────────
function WsSidebar({ collapsed = false, active = 'dashboard', onNav, theme }) {
  const items = [
    { id: 'dashboard', label: '대시보드', icon: I.Dashboard },
    { id: 'settlement', label: '정산/매출', icon: I.Wallet, badge: '12' },
    { id: 'branch', label: '지점 관리', icon: I.Building },
    { id: 'finance', label: '재무/회계', icon: I.Chart },
    { id: 'reports', label: '리포트', icon: I.Report },
    { id: 'members', label: '회원', icon: I.Users },
  ];
  const bottom = [
    { id: 'notification', label: '알림', icon: I.Bell, badge: '3' },
    { id: 'settings', label: '설정', icon: I.Settings },
  ];
  const w = collapsed ? 76 : 240;
  return (
    <aside style={{
      width: w, flexShrink: 0,
      background: 'var(--surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      transition: 'width .25s ease',
      height: '100%',
    }}>
      <div style={{
        padding: collapsed ? '20px 16px' : '20px 22px',
        display: 'flex', alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'flex-start',
      }}>
        <WsLogo size={28} withWordmark={!collapsed}/>
      </div>

      <nav style={{ padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {!collapsed && <div style={{ fontSize: 10.5, color: 'var(--ink-3)', letterSpacing: '0.06em', fontWeight: 700, padding: '12px 10px 6px' }}>WORKSPACE</div>}
        {items.map(it => <SidebarRow key={it.id} item={it} active={active === it.id} collapsed={collapsed} onClick={() => onNav?.(it.id)} />)}
      </nav>

      <div style={{ marginTop: 'auto', padding: '8px 12px 14px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {bottom.map(it => <SidebarRow key={it.id} item={it} active={active === it.id} collapsed={collapsed} onClick={() => onNav?.(it.id)} />)}
        <SidebarUser collapsed={collapsed}/>
      </div>
    </aside>
  );
}

function SidebarRow({ item, active, collapsed, onClick }) {
  const Icon = item.icon;
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: collapsed ? '10px' : '9px 12px',
        justifyContent: collapsed ? 'center' : 'flex-start',
        border: 0, background: active ? 'var(--surface-2)' : 'transparent',
        color: active ? 'var(--ink)' : 'var(--ink-2)',
        borderRadius: 10, position: 'relative',
        fontSize: 13.5, fontWeight: active ? 600 : 500,
        letterSpacing: '-0.01em',
        transition: 'background .15s, color .15s',
        textAlign: 'left',
      }}
      onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--surface-2)'; }}
      onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; }}
    >
      {active && !collapsed && (
        <span style={{ position: 'absolute', left: -12, top: 8, bottom: 8, width: 3, borderRadius: 2, background: 'var(--laon-red)' }} />
      )}
      <Icon size={18}/>
      {!collapsed && <span style={{ flex: 1 }}>{item.label}</span>}
      {!collapsed && item.badge && (
        <span style={{
          fontSize: 10.5, fontWeight: 700, color: '#fff',
          background: 'var(--laon-red)',
          borderRadius: 999, padding: '2px 7px', minWidth: 20, textAlign: 'center',
        }}>{item.badge}</span>
      )}
      {collapsed && item.badge && (
        <span style={{ position: 'absolute', top: 7, right: 12, width: 7, height: 7, borderRadius: 999, background: 'var(--laon-red)' }} />
      )}
    </button>
  );
}

function SidebarUser({ collapsed }) {
  return (
    <div style={{
      marginTop: 10, padding: collapsed ? '10px' : '10px 12px',
      borderTop: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', gap: 10,
      justifyContent: collapsed ? 'center' : 'flex-start',
    }}>
      <Avatar name="김재영" />
      {!collapsed && (
        <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, flex: 1 }}>
          <span style={{ fontSize: 12.5, fontWeight: 600 }}>김재영 본부장</span>
          <span style={{ fontSize: 11, color: 'var(--ink-3)' }}>경영지원본부 · 관리자</span>
        </div>
      )}
    </div>
  );
}

function Avatar({ name = 'KR', size = 32, color }) {
  const initials = name.length >= 2 ? name.slice(-2) : name;
  const hue = color || ['#E60028', '#3963A8', '#2E7D5B', '#B86E1F', '#7340B7'][name.charCodeAt(0) % 5];
  return (
    <div style={{
      width: size, height: size, borderRadius: 999,
      background: hue, color: '#fff',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.38, fontWeight: 700,
      letterSpacing: '-0.02em',
      flexShrink: 0,
    }}>{initials}</div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Topbar
// ──────────────────────────────────────────────────────────────────────
function WsTopbar({ title, breadcrumbs, right, onMenu }) {
  return (
    <header style={{
      padding: '18px 28px',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', gap: 16,
      background: 'var(--surface)',
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        {breadcrumbs && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--ink-3)', marginBottom: 4 }}>
            {breadcrumbs.map((b, i) => (
              <React.Fragment key={i}>
                {i > 0 && <I.ChevronRight size={12}/>}
                <span style={i === breadcrumbs.length - 1 ? { color: 'var(--ink-2)', fontWeight: 500 } : {}}>{b}</span>
              </React.Fragment>
            ))}
          </div>
        )}
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }}>{title}</h1>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <SearchBar/>
        <button style={iconBtn}><I.Bell size={18}/><span style={dotBadge}/></button>
        {right}
      </div>
    </header>
  );
}

const iconBtn = {
  width: 36, height: 36, borderRadius: 10,
  background: 'transparent', border: '1px solid var(--border)',
  color: 'var(--ink-2)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
  position: 'relative', cursor: 'pointer',
};
const dotBadge = {
  position: 'absolute', top: 7, right: 8, width: 7, height: 7, borderRadius: 999,
  background: 'var(--laon-red)', boxShadow: '0 0 0 2px var(--surface)',
};

function SearchBar({ width = 240 }) {
  return (
    <div style={{
      width, height: 36, display: 'flex', alignItems: 'center', gap: 8,
      padding: '0 12px', borderRadius: 10,
      background: 'var(--surface-2)', color: 'var(--ink-3)',
      fontSize: 13,
    }}>
      <I.Search size={16}/>
      <span style={{ flex: 1 }}>지점, 거래내역 검색...</span>
      <kbd style={{
        fontSize: 10, padding: '2px 5px', borderRadius: 4,
        background: 'var(--surface)', color: 'var(--ink-3)',
        border: '1px solid var(--border)',
        fontFamily: 'var(--font-mono)',
      }}>⌘K</kbd>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  KPI Cards
// ──────────────────────────────────────────────────────────────────────
function KPI({ label, value, sub, delta, sparkline, tone = 'neutral', chartType = 'area', currency = '원' }) {
  const color = tone === 'red' ? 'var(--laon-red)' : tone === 'pos' ? 'var(--pos)' : 'var(--ink)';
  return (
    <WsCard style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 12.5, color: 'var(--ink-3)', fontWeight: 500 }}>{label}</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 8 }}>
            <span className="ws-tnum" style={{ fontSize: 28, fontWeight: 700, color, letterSpacing: '-0.025em', lineHeight: 1.1 }}>{value}</span>
            {currency && <span style={{ fontSize: 13, color: 'var(--ink-3)', fontWeight: 500 }}>{currency}</span>}
          </div>
          {sub && <div style={{ fontSize: 11.5, color: 'var(--ink-3)', marginTop: 4 }}>{sub}</div>}
        </div>
        {delta != null && <WsDelta value={delta} big/>}
      </div>
      {sparkline && (
        <div style={{ height: 44, marginTop: 'auto' }}>
          {chartType === 'bar' ? <MiniBars data={sparkline} color={tone === 'red' ? 'var(--laon-red)' : 'var(--ink)'}/>
            : chartType === 'line' ? <MiniLine data={sparkline} color={tone === 'red' ? 'var(--laon-red)' : 'var(--ink)'}/>
            : <MiniArea data={sparkline} color={tone === 'red' ? 'var(--laon-red)' : 'var(--ink)'}/>}
        </div>
      )}
    </WsCard>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Mini charts (SVG)
// ──────────────────────────────────────────────────────────────────────
function MiniArea({ data, color = 'var(--ink)', height = 44 }) {
  const w = 100, h = height;
  const max = Math.max(...data), min = Math.min(...data);
  const r = max - min || 1;
  const pts = data.map((v, i) => [i * (w / (data.length - 1)), h - 4 - ((v - min) / r) * (h - 8)]);
  const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
  const fillPath = `${path} L${w},${h} L0,${h} Z`;
  const gid = useMemo(() => `g-${Math.random().toString(36).slice(2, 7)}`, []);
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" width="100%" height="100%">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity="0.18"/>
          <stop offset="1" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <path d={fillPath} fill={`url(#${gid})`}/>
      <path d={path} fill="none" stroke={color} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke"/>
    </svg>
  );
}

function MiniLine({ data, color = 'var(--ink)', height = 44 }) {
  const w = 100, h = height;
  const max = Math.max(...data), min = Math.min(...data);
  const r = max - min || 1;
  const pts = data.map((v, i) => `${i * (w / (data.length - 1))},${h - 4 - ((v - min) / r) * (h - 8)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" width="100%" height="100%">
      <polyline fill="none" stroke={color} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" points={pts} vectorEffect="non-scaling-stroke"/>
    </svg>
  );
}

function MiniBars({ data, color = 'var(--ink)', height = 44 }) {
  const w = 100, h = height;
  const max = Math.max(...data);
  const bw = w / data.length;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" width="100%" height="100%">
      {data.map((v, i) => {
        const bh = (v / max) * (h - 6);
        return <rect key={i} x={i * bw + 1.5} y={h - bh} width={bw - 3} height={bh} fill={color} fillOpacity={i === data.length - 1 ? 1 : 0.45} rx="1.5"/>;
      })}
    </svg>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Big chart: revenue vs cost (area), and combo bar+line, donut
// ──────────────────────────────────────────────────────────────────────
function ChartArea({ series, labels, height = 220, chartType = 'area' }) {
  // series: [{name, values, color}]
  const W = 600, H = height, padL = 44, padR = 16, padT = 16, padB = 28;
  const allValues = series.flatMap(s => s.values);
  const max = Math.max(...allValues) * 1.1;
  const min = 0;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;
  const x = (i) => padL + (i / (labels.length - 1)) * innerW;
  const y = (v) => padT + (1 - (v - min) / (max - min)) * innerH;
  const gridSteps = 4;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} style={{ display: 'block' }}>
      {/* grid */}
      {Array.from({ length: gridSteps + 1 }, (_, i) => {
        const yp = padT + (i / gridSteps) * innerH;
        const v = max - (i / gridSteps) * (max - min);
        return (
          <g key={i}>
            <line x1={padL} x2={W - padR} y1={yp} y2={yp} stroke="var(--border)" strokeWidth="1"/>
            <text x={padL - 8} y={yp + 3} fontSize="10" textAnchor="end" fill="var(--ink-3)" fontFamily="var(--font-mono)">{Math.round(v / 1e6)}M</text>
          </g>
        );
      })}
      {/* labels */}
      {labels.map((lab, i) => (
        <text key={i} x={x(i)} y={H - 8} fontSize="10.5" textAnchor="middle" fill="var(--ink-3)">{lab}</text>
      ))}
      {series.map((s, si) => {
        const pts = s.values.map((v, i) => [x(i), y(v)]);
        const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
        const fillPath = `${path} L${x(s.values.length - 1)},${H - padB} L${padL},${H - padB} Z`;
        const gid = `area-${si}-${Math.random().toString(36).slice(2, 6)}`;
        if (chartType === 'bar') {
          const bw = (innerW / s.values.length) / series.length * 0.7;
          return s.values.map((v, i) => (
            <rect key={i} x={x(i) - (bw * series.length)/2 + si * bw} y={y(v)} width={bw} height={H - padB - y(v)} fill={s.color} rx="2"/>
          ));
        }
        return (
          <g key={si}>
            {chartType === 'area' && (
              <>
                <defs>
                  <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0" stopColor={s.color} stopOpacity="0.22"/>
                    <stop offset="1" stopColor={s.color} stopOpacity="0"/>
                  </linearGradient>
                </defs>
                <path d={fillPath} fill={`url(#${gid})`}/>
              </>
            )}
            <path d={path} fill="none" stroke={s.color} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round"/>
            {pts.map((p, i) => i === pts.length - 1 ? <circle key={i} cx={p[0]} cy={p[1]} r="3.5" fill="var(--surface)" stroke={s.color} strokeWidth="2"/> : null)}
          </g>
        );
      })}
    </svg>
  );
}

function Donut({ segments, size = 160, thickness = 22, center }) {
  // segments: [{label, value, color}]
  const total = segments.reduce((a, s) => a + s.value, 0);
  const r = size / 2 - thickness / 2;
  const c = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--surface-2)" strokeWidth={thickness}/>
        {segments.map((s, i) => {
          const len = (s.value / total) * c;
          const el = <circle key={i} cx={size/2} cy={size/2} r={r} fill="none" stroke={s.color} strokeWidth={thickness} strokeDasharray={`${len} ${c - len}`} strokeDashoffset={-offset} strokeLinecap="butt"/>;
          offset += len;
          return el;
        })}
      </svg>
      {center && <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>{center}</div>}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Drawer / Side panel
// ──────────────────────────────────────────────────────────────────────
function Drawer({ open, onClose, width = 460, children }) {
  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: 'absolute', inset: 0, background: 'rgba(31,27,27,0.32)',
          opacity: open ? 1 : 0, pointerEvents: open ? 'auto' : 'none',
          transition: 'opacity .2s ease', zIndex: 10,
        }}
      />
      <aside style={{
        position: 'absolute', top: 0, right: 0, bottom: 0,
        width, background: 'var(--surface)',
        borderLeft: '1px solid var(--border)',
        boxShadow: 'var(--shadow-lg)', zIndex: 11,
        transform: open ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform .25s cubic-bezier(.4,.0,.2,1)',
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {children}
      </aside>
    </>
  );
}

// ──────────────────────────────────────────────────────────────────────
// Expose globally
// ──────────────────────────────────────────────────────────────────────
Object.assign(window, {
  WsLogo, WsCard, WsBtn, WsTag, WsDelta, WsSidebar, WsTopbar, SearchBar,
  KPI, MiniArea, MiniLine, MiniBars, ChartArea, Donut, Drawer, Avatar,
  wsKRW, wsPct, iconBtn,
});
