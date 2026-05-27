// app.jsx — WebSettle: DesignCanvas mount + Tweaks

const { useState, useEffect } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "light",
  "density": "regular",
  "chartType": "area",
  "sidebarCollapsed": false,
  "accent": "#E60028"
}/*EDITMODE-END*/;

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  // Inject accent as CSS var globally
  useEffect(() => {
    document.documentElement.style.setProperty('--laon-red', t.accent || '#E60028');
  }, [t.accent]);

  // Shared screen props
  const sp = {
    sidebarCollapsed: t.sidebarCollapsed,
    chartType: t.chartType,
  };

  // Theme/density wrapper for each artboard
  const wrap = (children) => (
    <div data-theme={t.theme} data-density={t.density} style={{ width: '100%', height: '100%' }}>
      {children}
    </div>
  );

  // Mobile device frame (custom, simple — content already has its own status bar)
  const phone = (children) => (
    <div data-theme={t.theme} data-density={t.density} style={{
      width: 390, height: 844, borderRadius: 44, overflow: 'hidden',
      background: '#000',
      boxShadow: '0 0 0 8px #1A1716, 0 30px 60px rgba(31,27,27,0.18)',
      position: 'relative',
    }}>
      {/* Dynamic island */}
      <div style={{
        position: 'absolute', top: 11, left: '50%', transform: 'translateX(-50%)',
        width: 122, height: 35, borderRadius: 22, background: '#000', zIndex: 50,
      }}/>
      <div style={{ width: '100%', height: '100%', overflow: 'hidden', borderRadius: 36 }}>
        {children}
      </div>
      {/* Home indicator */}
      <div style={{
        position: 'absolute', bottom: 8, left: '50%', transform: 'translateX(-50%)',
        width: 130, height: 5, borderRadius: 100, background: 'rgba(0,0,0,0.4)', zIndex: 60,
      }}/>
    </div>
  );

  return (
    <>
      <DesignCanvas defaultZoom={0.55}>
        <DCSection
          id="desktop-auth"
          title="데스크탑 · 인증"
          subtitle="LAON SPORTS 사내 계정 로그인"
        >
          <DCArtboard id="login" label="01 · 로그인" width={1280} height={800}>
            {wrap(<ScreenLogin width={1280} height={800}/>)}
          </DCArtboard>
        </DCSection>

        <DCSection
          id="desktop-dashboard"
          title="데스크탑 · 메인 대시보드"
          subtitle="동일한 데이터, 세 가지 정보 우선순위 · 한 가지를 골라 본 채택안으로 진행"
        >
          <DCArtboard id="dash-a" label="A · 정산/매출 중심" width={1440} height={900}>
            {wrap(<DashboardA width={1440} height={900} {...sp}/>)}
          </DCArtboard>
          <DCArtboard id="dash-b" label="B · 지점 중심" width={1440} height={900}>
            {wrap(<DashboardB width={1440} height={900} {...sp}/>)}
          </DCArtboard>
          <DCArtboard id="dash-c" label="C · 손익 중심" width={1440} height={900}>
            {wrap(<DashboardC width={1440} height={900} {...sp}/>)}
          </DCArtboard>
        </DCSection>

        <DCSection
          id="desktop-detail"
          title="데스크탑 · 드릴다운"
          subtitle="행 클릭 → 사이드 패널 슬라이드인. 목록은 유지된다."
        >
          <DCArtboard id="settlement" label="정산 · 매출 상세" width={1440} height={900}>
            {wrap(<ScreenSettlement width={1440} height={900} {...sp}/>)}
          </DCArtboard>
        </DCSection>

        <DCSection
          id="desktop-reports"
          title="데스크탑 · 리포트"
          subtitle="기간별 분석 · 히트맵 · VIP TOP 5"
        >
          <DCArtboard id="reports" label="리포트 (월간)" width={1440} height={900}>
            {wrap(<ScreenReports width={1440} height={900} {...sp}/>)}
          </DCArtboard>
        </DCSection>

        <DCSection
          id="desktop-pdf"
          title="데스크탑 · 정산서 PDF"
          subtitle="출력/이메일/인쇄 · 사이드 패널에서 옵션 조절"
        >
          <DCArtboard id="pdf" label="정산서 미리보기" width={1440} height={900}>
            {wrap(<ScreenSettlementPDF width={1440} height={900} {...sp}/>)}
          </DCArtboard>
        </DCSection>

        <DCSection
          id="mobile"
          title="모바일 · 네이티브 앱 느낌"
          subtitle="동일 디자인 시스템을 모바일로 압축. 하단 탭바 + 풀스크린 차트."
        >
          <DCArtboard id="m-login" label="로그인" width={390} height={844}>
            {phone(<MobileLogin/>)}
          </DCArtboard>
          <DCArtboard id="m-home" label="홈 · KPI" width={390} height={844}>
            {phone(<MobileHome chartType={t.chartType}/>)}
          </DCArtboard>
          <DCArtboard id="m-settle" label="정산 상세 (드릴다운)" width={390} height={844}>
            {phone(<MobileSettlement chartType={t.chartType}/>)}
          </DCArtboard>
        </DCSection>
      </DesignCanvas>

      <TweaksPanel>
        <TweakSection label="화면" />
        <TweakRadio  label="테마" value={t.theme}
                     options={['light', 'dark']}
                     onChange={(v) => setTweak('theme', v)} />
        <TweakRadio  label="밀도" value={t.density}
                     options={['compact', 'regular', 'comfortable']}
                     onChange={(v) => setTweak('density', v)} />
        <TweakToggle label="사이드바 축소" value={t.sidebarCollapsed}
                     onChange={(v) => setTweak('sidebarCollapsed', v)} />

        <TweakSection label="시각화" />
        <TweakRadio  label="차트 종류" value={t.chartType}
                     options={['area', 'line', 'bar']}
                     onChange={(v) => setTweak('chartType', v)} />
        <TweakColor  label="포인트 컬러" value={t.accent}
                     options={['#E60028', '#C00022', '#FF4D5E', '#9E1429']}
                     onChange={(v) => setTweak('accent', v)} />
      </TweaksPanel>
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
