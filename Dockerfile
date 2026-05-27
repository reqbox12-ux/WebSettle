FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 데이터 폴더 / 업로드 폴더 생성
RUN mkdir -p /app/data /app/static/uploads

# 시작 스크립트 실행 권한
RUN chmod +x /app/start.sh

# 포트 노출 (ERP: 8501, 지점포털: 8502)
EXPOSE 8501 8502

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["/bin/bash", "/app/start.sh"]
