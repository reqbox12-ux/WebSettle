# 백업 및 복구 가이드

## 📋 백업 시스템 구조

```
WEBAPP/
├── backups/          # 자동 백업 저장소 (최근 7개만 유지)
├── data/
│   └── settlement.db # 현재 데이터베이스
├── mapping/          # 분류 규칙, 지점 매핑
├── backup.py         # 백업 생성 스크립트
├── restore.py        # 복구 스크립트
└── .git/             # Git 버전 관리
```

## 🔄 자동 백업

### 방법 1: 수동 실행
```powershell
python backup.py
```

### 방법 2: Windows 작업 스케줄러 (일일 자동)

1. `backup_daily.bat` 우클릭 → 속성 → 위치 복사
2. 작업 스케줄러 열기 (검색: "작업 스케줄러")
3. 오른쪽 패널 "기본 작업 만들기..."
   - 이름: "Settlement Backup"
   - 트리거: 매일 자정
   - 작업: `backup_daily.bat` 파일 경로 입력
   - 확인

## 🔙 복구하기

### 빠른 복구 (최근 백업)
```powershell
python restore.py
```

그러면:
1. 사용 가능한 백업 목록 표시
2. 복구할 백업 번호 입력
3. 현재 DB는 `broken_TIMESTAMP.db` 로 저장됨
4. 선택한 백업에서 복구 완료

### 예시:
```
=== Available Backups ===
1. settlement_20260514_130000.db (5.23MB)
2. settlement_20260513_130000.db (5.20MB)
3. settlement_20260512_130000.db (5.18MB)

Enter backup number to restore (0 to cancel): 1
✓ Restored from: settlement_20260514_130000.db
```

## 📊 Git 버전 관리

모든 코드 변경사항은 Git에 자동 추적됩니다.

### 코드 변경 후 커밋
```powershell
git add .
git commit -m "설명: 변경 내용"
```

### 이전 버전으로 되돌리기
```powershell
# 최근 1개 커밋 취소
git revert HEAD

# 특정 버전으로 복구
git log  # 커밋 ID 확인
git checkout <commit-id>
```

## 🛡️ 백업 종류

### 1. 데이터베이스 (settlement.db)
- 모든 거래 기록, 분류 규칙, 급여 정보
- 자동 백업: 매일 최신 버전 저장
- 최대 유지: 7개 파일 (자동 삭제)

### 2. 매핑 파일 (mapping/)
- branch_mapping.json: 카드사 → 지점 매핑
- keyword_rules.json: 자동 분류 규칙
- 자동 백업: 매일 함께 저장

### 3. 코드 (Git)
- app.py, modules/, mapping/
- 모든 변경사항 추적
- GitHub 업로드하면 클라우드 백업됨

## ⚠️ 응급 복구

### 데이터베이스 손상 시
```powershell
# 백업 폴더에서 가장 최근 파일 확인
ls backups/settlement_*.db | Sort-Object LastWriteTime -Descending

# 복구
python restore.py
```

### 코드 손상 시
```powershell
# 이전 버전 확인
git log --oneline

# 특정 파일만 복구
git checkout <commit-id> -- app.py
```

## 📈 백업 용량 관리

- 각 백업: ~5-10MB
- 유지 개수: 7개 (약 35-70MB)
- 자동 정리: `backup.py` 실행 시 오래된 파일 삭제

## ✅ 체크리스트

- [ ] 첫 백업 실행됨 (`backups/` 폴더 확인)
- [ ] 코드 Git 커밋됨 (`git log` 확인)
- [ ] 작업 스케줄러 설정 완료 (옵션)

## 🆘 문제 해결

**"No backups found"**
→ `backup.py` 먼저 실행

**"Backup 폴더가 가득 참"**
→ `backups/` 에서 오래된 파일 수동 삭제

**"Git 초기화 실패"**
→ `.git` 폴더 삭제 후 `git init` 다시 실행
