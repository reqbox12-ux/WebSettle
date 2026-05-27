// icons.jsx — Lucide-style line icons (1.5px stroke). All 20×20 viewBox.
// All icons accept {size, color, strokeWidth, ...rest}.

const Ic = ({ d, size = 20, color = 'currentColor', sw = 1.6, fill = 'none', children, ...rest }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size} height={size} viewBox="0 0 20 20"
    fill={fill} stroke={color} strokeWidth={sw}
    strokeLinecap="round" strokeLinejoin="round"
    style={{ flexShrink: 0, display: 'block' }}
    {...rest}
  >
    {d ? <path d={d} /> : children}
  </svg>
);

const Icons = {
  Home: (p) => <Ic {...p}><path d="M3 9.5 10 3l7 6.5"/><path d="M5 9v8h4v-5h2v5h4V9"/></Ic>,
  Dashboard: (p) => <Ic {...p}><rect x="3" y="3" width="6.5" height="8" rx="1.5"/><rect x="10.5" y="3" width="6.5" height="5" rx="1.5"/><rect x="3" y="12" width="6.5" height="5" rx="1.5"/><rect x="10.5" y="9" width="6.5" height="8" rx="1.5"/></Ic>,
  Wallet: (p) => <Ic {...p}><path d="M3 6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6Z"/><path d="M14 11h2"/><path d="M3 8h14"/></Ic>,
  Receipt: (p) => <Ic {...p}><path d="M5 2v16l2-1.5L9 18l2-1.5L13 18l2-1.5V2"/><path d="M7 6h8M7 9h8M7 12h5"/></Ic>,
  Branch: (p) => <Ic {...p}><path d="M3 17V8.5L7 6l3 1.5L14 5l3 1.5V17"/><path d="M7 11v6M14 8v9"/><path d="M3 17h14"/></Ic>,
  Chart: (p) => <Ic {...p}><path d="M3 3v14h14"/><path d="M6 13l3-4 3 2 4-6"/></Ic>,
  Report: (p) => <Ic {...p}><rect x="4" y="3" width="12" height="14" rx="2"/><path d="M7 8h6M7 11h6M7 14h3"/></Ic>,
  User: (p) => <Ic {...p}><circle cx="10" cy="7" r="3"/><path d="M4 17c1.2-3 3.6-4 6-4s4.8 1 6 4"/></Ic>,
  Users: (p) => <Ic {...p}><circle cx="8" cy="7" r="3"/><path d="M2 17c1-3 3-4 6-4s5 1 6 4"/><circle cx="14.5" cy="6" r="2.4"/><path d="M14 13c2.2.1 3.6 1.3 4 4"/></Ic>,
  Bell: (p) => <Ic {...p}><path d="M5 14V9a5 5 0 0 1 10 0v5"/><path d="M3.5 14h13"/><path d="M8.5 17a1.6 1.6 0 0 0 3 0"/></Ic>,
  Search: (p) => <Ic {...p}><circle cx="9" cy="9" r="5.5"/><path d="m13 13 4 4"/></Ic>,
  Settings: (p) => <Ic {...p}><circle cx="10" cy="10" r="2.5"/><path d="M10 2v2.5M10 15.5V18M2 10h2.5M15.5 10H18M4.3 4.3l1.8 1.8M13.9 13.9l1.8 1.8M15.7 4.3l-1.8 1.8M6.1 13.9l-1.8 1.8"/></Ic>,
  Filter: (p) => <Ic {...p}><path d="M3 4h14l-5.5 7v5l-3 1.5v-6.5L3 4Z"/></Ic>,
  Download: (p) => <Ic {...p}><path d="M10 3v10"/><path d="m6.5 9.5 3.5 3.5 3.5-3.5"/><path d="M3.5 16h13"/></Ic>,
  Upload: (p) => <Ic {...p}><path d="M10 17V7"/><path d="m6.5 10.5 3.5-3.5 3.5 3.5"/><path d="M3.5 16h13"/></Ic>,
  Calendar: (p) => <Ic {...p}><rect x="3" y="4" width="14" height="13" rx="2"/><path d="M3 8h14M7 2.5v3M13 2.5v3"/></Ic>,
  ChevronDown: (p) => <Ic {...p}><path d="m5 7.5 5 5 5-5"/></Ic>,
  ChevronUp: (p) => <Ic {...p}><path d="m5 12.5 5-5 5 5"/></Ic>,
  ChevronRight: (p) => <Ic {...p}><path d="m7.5 5 5 5-5 5"/></Ic>,
  ChevronLeft: (p) => <Ic {...p}><path d="m12.5 5-5 5 5 5"/></Ic>,
  ArrowUp: (p) => <Ic {...p}><path d="M10 4v12"/><path d="m5 9 5-5 5 5"/></Ic>,
  ArrowDown: (p) => <Ic {...p}><path d="M10 16V4"/><path d="m5 11 5 5 5-5"/></Ic>,
  ArrowUpRight: (p) => <Ic {...p}><path d="M6 14 14 6"/><path d="M7 6h7v7"/></Ic>,
  ArrowDownRight: (p) => <Ic {...p}><path d="M6 6 14 14"/><path d="M14 7v7h-7"/></Ic>,
  Plus: (p) => <Ic {...p}><path d="M10 4v12M4 10h12"/></Ic>,
  X: (p) => <Ic {...p}><path d="M5 5l10 10M15 5 5 15"/></Ic>,
  More: (p) => <Ic {...p}><circle cx="5" cy="10" r="1.1" fill="currentColor"/><circle cx="10" cy="10" r="1.1" fill="currentColor"/><circle cx="15" cy="10" r="1.1" fill="currentColor"/></Ic>,
  Check: (p) => <Ic {...p}><path d="m4.5 10.5 3.5 3.5 7.5-8"/></Ic>,
  Eye: (p) => <Ic {...p}><path d="M2 10s2.5-5 8-5 8 5 8 5-2.5 5-8 5-8-5-8-5Z"/><circle cx="10" cy="10" r="2.5"/></Ic>,
  EyeOff: (p) => <Ic {...p}><path d="m3 3 14 14"/><path d="M6.5 6.5C4 8 2 10 2 10s2.5 5 8 5c1.4 0 2.7-.3 3.8-.8"/><path d="M9 5.1c.3 0 .7-.1 1-.1 5.5 0 8 5 8 5s-.7 1.4-2 2.7"/></Ic>,
  Lock: (p) => <Ic {...p}><rect x="4" y="9" width="12" height="9" rx="1.5"/><path d="M6.5 9V7a3.5 3.5 0 0 1 7 0v2"/></Ic>,
  Mail: (p) => <Ic {...p}><rect x="3" y="4.5" width="14" height="11" rx="2"/><path d="m3.5 6 6.5 5 6.5-5"/></Ic>,
  Logout: (p) => <Ic {...p}><path d="M9 4H5a1.5 1.5 0 0 0-1.5 1.5v9A1.5 1.5 0 0 0 5 16h4"/><path d="m13 7 3 3-3 3"/><path d="M16 10H7"/></Ic>,
  Card: (p) => <Ic {...p}><rect x="2.5" y="5" width="15" height="10" rx="2"/><path d="M2.5 8.5h15M5 12h2"/></Ic>,
  Refund: (p) => <Ic {...p}><path d="M3 10a7 7 0 1 1 2.2 5.1"/><path d="M3 17v-3.5h3.5"/></Ic>,
  TrendingUp: (p) => <Ic {...p}><path d="m3 14 5-5 3 3 6-7"/><path d="M12 5h5v5"/></Ic>,
  PieIcon: (p) => <Ic {...p}><path d="M10 3v7l6 4a7 7 0 1 1-6-11Z"/><path d="M11 3a7 7 0 0 1 6 6h-6V3Z"/></Ic>,
  Dot: (p) => <Ic {...p} fill="currentColor"><circle cx="10" cy="10" r="3"/></Ic>,
  Doc: (p) => <Ic {...p}><path d="M5 3h7l3 3v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z"/><path d="M12 3v3h3"/></Ic>,
  Print: (p) => <Ic {...p}><rect x="5" y="3" width="10" height="5"/><rect x="3" y="8" width="14" height="7" rx="1.5"/><rect x="6" y="12" width="8" height="5"/></Ic>,
  Building: (p) => <Ic {...p}><rect x="4" y="3" width="12" height="14" rx="1"/><path d="M7 6h2M11 6h2M7 9h2M11 9h2M7 12h2M11 12h2"/><path d="M8.5 17v-3h3v3"/></Ic>,
  Home2: (p) => <Ic {...p}><path d="M3 9 10 3l7 6"/><path d="M5 8v9h10V8"/></Ic>,
};

// Bottom-tab specific filled variants
Icons.HomeFilled = (p) => <Ic {...p} fill="currentColor"><path d="M3 9 10 3l7 6v8a1 1 0 0 1-1 1h-3v-6H9v6H4a1 1 0 0 1-1-1V9Z"/></Ic>;

window.Icons = Icons;
