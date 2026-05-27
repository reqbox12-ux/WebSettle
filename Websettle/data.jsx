// data.jsx — Mock data for WebSettle (LAON SPORTS 사내 정산 대시보드)

const wsData = {
  today: '2026년 05월 16일 (토)',
  period: '2026년 4월',
  branches: [
    { id: 'gn',  name: '강남 본점',     code: 'GN-01', region: '서울',   members: 1842, revenue: 384200000, costs: 168400000, settled: 'paid',    delta: 8.2,  trend: [220, 268, 245, 290, 312, 348, 384] },
    { id: 'bd',  name: '분당점',         code: 'BD-02', region: '경기',   members: 1268, revenue: 264800000, costs: 121200000, settled: 'pending', delta: 3.1,  trend: [198, 210, 232, 218, 244, 258, 264] },
    { id: 'js',  name: '잠실점',         code: 'JS-03', region: '서울',   members: 1410, revenue: 301600000, costs: 138900000, settled: 'paid',    delta: 12.4, trend: [184, 192, 218, 232, 256, 282, 301] },
    { id: 'sd',  name: '송도점',         code: 'SD-04', region: '인천',   members:  892, revenue: 184200000, costs:  91300000, settled: 'paid',    delta: -2.1, trend: [188, 192, 184, 196, 178, 192, 184] },
    { id: 'gk',  name: '광교점',         code: 'GK-05', region: '경기',   members: 1024, revenue: 215800000, costs: 102400000, settled: 'pending', delta: 5.6,  trend: [172, 184, 192, 204, 198, 212, 215] },
    { id: 'hd',  name: '해운대점',       code: 'HD-06', region: '부산',   members:  768, revenue: 142400000, costs:  78600000, settled: 'overdue', delta: -8.4, trend: [168, 162, 154, 142, 148, 152, 142] },
    { id: 'dj',  name: '둔산점',         code: 'DJ-07', region: '대전',   members:  680, revenue: 128600000, costs:  64900000, settled: 'paid',    delta: 4.2,  trend: [108, 118, 122, 116, 124, 126, 128] },
    { id: 'dg',  name: '수성점',         code: 'DG-08', region: '대구',   members:  712, revenue: 134800000, costs:  68200000, settled: 'paid',    delta: 1.9,  trend: [124, 128, 132, 130, 128, 132, 134] },
  ],
  // monthly revenue vs cost (Nov..Apr)
  monthly: {
    labels: ['11월','12월','1월','2월','3월','4월'],
    revenue: [1450000000, 1620000000, 1680000000, 1540000000, 1720000000, 1956000000],
    cost:    [ 720000000,  788000000,  812000000,  792000000,  864000000,  933000000],
    profit:  [ 730000000,  832000000,  868000000,  748000000,  856000000, 1023000000],
  },
  payments: [
    { id: 'PMT-26050912', ts: '2026-05-16 14:42', branch: '강남 본점',  member: '이서연', amount:  890000, method: '카드',   status: 'success', type: '월회비'   },
    { id: 'PMT-26050911', ts: '2026-05-16 14:21', branch: '잠실점',     member: '박지훈', amount:  120000, method: '현장결제', status: 'success', type: 'PT 10회' },
    { id: 'PMT-26050910', ts: '2026-05-16 13:58', branch: '분당점',     member: '최유나', amount: 2400000, method: '계좌이체', status: 'success', type: '연회원'   },
    { id: 'PMT-26050909', ts: '2026-05-16 13:42', branch: '광교점',     member: '김도현', amount:  890000, method: '카드',   status: 'pending', type: '월회비'   },
    { id: 'PMT-26050908', ts: '2026-05-16 13:18', branch: '강남 본점',  member: '한지민', amount: 1200000, method: '카드',   status: 'success', type: 'PT 30회' },
    { id: 'PMT-26050907', ts: '2026-05-16 12:54', branch: '송도점',     member: '오민석', amount:  890000, method: '카드',   status: 'refunded',type: '월회비'   },
    { id: 'PMT-26050906', ts: '2026-05-16 12:31', branch: '해운대점',   member: '윤서아', amount:  450000, method: '카드',   status: 'success', type: '필라테스' },
    { id: 'PMT-26050905', ts: '2026-05-16 12:08', branch: '둔산점',     member: '정현우', amount:  890000, method: '계좌이체', status: 'success', type: '월회비'   },
  ],
  alerts: [
    { id: 1, severity: 'high',   title: '해운대점 정산 연체',  desc: '4월 정산금 14.2백만 원 7일 경과', when: '2시간 전' },
    { id: 2, severity: 'medium', title: '분당점 환불 급증',     desc: '전주 대비 +218%, 검토 필요',         when: '4시간 전' },
    { id: 3, severity: 'low',    title: '광교점 결제 지연',     desc: 'PG사 정산 보류 건 3건',              when: '어제'    },
  ],
  expenses: [
    { label: '인건비',     value: 392000000, color: '#1F1B1B' },
    { label: '임대료',     value: 218000000, color: '#5B5450' },
    { label: '시설관리',   value: 142000000, color: '#9A918C' },
    { label: '마케팅',     value:  86000000, color: '#E60028' },
    { label: '소모품/장비', value:  64000000, color: '#C3BAB4' },
    { label: '기타',       value:  31000000, color: '#ECE7E2' },
  ],
};

window.wsData = wsData;
